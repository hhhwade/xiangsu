-- 行迹智能旅游路线规划软件
-- PostgreSQL 16 + PostGIS 3.x 数据库设计
--
-- 原则：规划结果是不可变快照；高德 POI 只保存规划所需最小字段；
--      用户身份/权限由应用层或外部 OIDC 提供，所有时间使用 timestamptz。

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
  CREATE TYPE transport_mode AS ENUM ('walking', 'riding', 'driving', 'transit');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE plan_status AS ENUM ('draft', 'ready', 'stale', 'failed', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Replace external_subject with the subject from OIDC/Auth0/your identity provider.
CREATE TABLE IF NOT EXISTS app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_subject text UNIQUE NOT NULL,
  display_name text,
  locale varchar(16) NOT NULL DEFAULT 'zh-CN',
  timezone varchar(64) NOT NULL DEFAULT 'Asia/Shanghai',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE IF NOT EXISTS destinations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name text NOT NULL,
  city_code varchar(32),               -- AMap city/adcode when known
  country_code char(2) NOT NULL DEFAULT 'CN',
  center geography(Point, 4326),
  boundary geometry(MultiPolygon, 4326),
  source text NOT NULL DEFAULT 'amap',
  source_ref text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (canonical_name, country_code)
);
CREATE INDEX IF NOT EXISTS destinations_center_gix ON destinations USING gist (center);
CREATE INDEX IF NOT EXISTS destinations_boundary_gix ON destinations USING gist (boundary);

-- A versioned, minimal snapshot rather than a full third-party POI mirror.
CREATE TABLE IF NOT EXISTS poi_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider varchar(32) NOT NULL DEFAULT 'amap',
  provider_poi_id varchar(128) NOT NULL,
  destination_id uuid REFERENCES destinations(id) ON DELETE SET NULL,
  name text NOT NULL,
  category_codes text[] NOT NULL DEFAULT '{}',
  display_type text,
  address text,
  location geography(Point, 4326) NOT NULL,
  opening_hours jsonb NOT NULL DEFAULT '{}'::jsonb,
  accessibility jsonb NOT NULL DEFAULT '{}'::jsonb,
  estimated_visit_minutes smallint CHECK (estimated_visit_minutes BETWEEN 5 AND 720),
  rating numeric(3,2) CHECK (rating >= 0 AND rating <= 5),
  price_level smallint CHECK (price_level BETWEEN 0 AND 5),
  raw_hash char(64),                  -- change detection, not raw third-party payload
  valid_from timestamptz NOT NULL DEFAULT now(),
  valid_until timestamptz,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider, provider_poi_id, valid_from)
);
CREATE INDEX IF NOT EXISTS poi_snapshots_location_gix ON poi_snapshots USING gist (location);
CREATE INDEX IF NOT EXISTS poi_snapshots_destination_idx ON poi_snapshots(destination_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS poi_snapshots_categories_gin ON poi_snapshots USING gin (category_codes);

-- Stores validated input. special_needs is personal preference data: encrypt at rest
-- or move to a protected profile table if policy requires it.
CREATE TABLE IF NOT EXISTS itinerary_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  destination_id uuid REFERENCES destinations(id) ON DELETE SET NULL,
  destination_input text NOT NULL,
  duration_value numeric(6,2) NOT NULL CHECK (duration_value > 0),
  duration_unit varchar(8) NOT NULL CHECK (duration_unit IN ('days', 'hours')),
  daily_hours numeric(4,2) NOT NULL CHECK (daily_hours BETWEEN 2 AND 16),
  transport transport_mode NOT NULL DEFAULT 'driving',
  preferences text[] NOT NULL DEFAULT '{}',
  budget_min numeric(12,2) CHECK (budget_min >= 0),
  budget_max numeric(12,2) CHECK (budget_max >= 0),
  adults smallint NOT NULL DEFAULT 1 CHECK (adults >= 0),
  children smallint NOT NULL DEFAULT 0 CHECK (children >= 0),
  has_elderly boolean NOT NULL DEFAULT false,
  needs_accessible boolean NOT NULL DEFAULT false,
  special_needs text,
  requested_start_at timestamptz,
  requested_start_location geography(Point, 4326),
  algorithm_version varchar(32) NOT NULL,
  source varchar(16) NOT NULL CHECK (source IN ('amap', 'fallback', 'mixed')),
  status plan_status NOT NULL DEFAULT 'draft',
  total_distance_m integer CHECK (total_distance_m >= 0),
  total_spots smallint CHECK (total_spots >= 0),
  backtrack_check boolean NOT NULL DEFAULT false,
  request_hash char(64),
  revision integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (budget_max IS NULL OR budget_min IS NULL OR budget_min <= budget_max),
  CHECK (adults + children >= 1)
);
CREATE INDEX IF NOT EXISTS itinerary_plans_owner_idx ON itinerary_plans(owner_id, created_at DESC) WHERE owner_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS itinerary_plans_request_hash_idx ON itinerary_plans(request_hash, created_at DESC);
CREATE INDEX IF NOT EXISTS itinerary_plans_start_location_gix ON itinerary_plans USING gist (requested_start_location);

CREATE TABLE IF NOT EXISTS itinerary_days (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid NOT NULL REFERENCES itinerary_plans(id) ON DELETE CASCADE,
  day_number smallint NOT NULL CHECK (day_number BETWEEN 1 AND 30),
  title text NOT NULL,
  theme text,
  color char(7) NOT NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
  visit_budget_minutes integer NOT NULL CHECK (visit_budget_minutes > 0),
  total_distance_m integer NOT NULL DEFAULT 0 CHECK (total_distance_m >= 0),
  total_visit_minutes integer NOT NULL DEFAULT 0 CHECK (total_visit_minutes >= 0),
  total_transport_minutes integer NOT NULL DEFAULT 0 CHECK (total_transport_minutes >= 0),
  total_buffer_minutes integer NOT NULL DEFAULT 0 CHECK (total_buffer_minutes >= 0),
  summary text,
  notices jsonb NOT NULL DEFAULT '[]'::jsonb,
  UNIQUE (plan_id, day_number)
);
CREATE INDEX IF NOT EXISTS itinerary_days_plan_idx ON itinerary_days(plan_id, day_number);

-- Snapshot every stop so exports and shares remain stable even if a provider POI changes.
CREATE TABLE IF NOT EXISTS itinerary_stops (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  day_id uuid NOT NULL REFERENCES itinerary_days(id) ON DELETE CASCADE,
  poi_snapshot_id uuid REFERENCES poi_snapshots(id) ON DELETE SET NULL,
  provider_poi_id varchar(128),
  stop_order smallint NOT NULL CHECK (stop_order BETWEEN 1 AND 12),
  name text NOT NULL,
  display_type text,
  location geography(Point, 4326) NOT NULL,
  estimated_visit_minutes smallint NOT NULL CHECK (estimated_visit_minutes BETWEEN 5 AND 720),
  arrival_at timestamptz NOT NULL,
  leave_at timestamptz NOT NULL,
  opening_hours_text text,
  tips text,
  user_locked boolean NOT NULL DEFAULT false, -- do not reorder this stop automatically
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (leave_at >= arrival_at),
  UNIQUE (day_id, stop_order)
);
CREATE INDEX IF NOT EXISTS itinerary_stops_day_idx ON itinerary_stops(day_id, stop_order);
CREATE INDEX IF NOT EXISTS itinerary_stops_location_gix ON itinerary_stops USING gist (location);

CREATE TABLE IF NOT EXISTS itinerary_legs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  day_id uuid NOT NULL REFERENCES itinerary_days(id) ON DELETE CASCADE,
  from_stop_id uuid NOT NULL REFERENCES itinerary_stops(id) ON DELETE CASCADE,
  to_stop_id uuid NOT NULL REFERENCES itinerary_stops(id) ON DELETE CASCADE,
  leg_order smallint NOT NULL CHECK (leg_order BETWEEN 1 AND 11),
  transport transport_mode NOT NULL,
  distance_m integer NOT NULL CHECK (distance_m >= 0),
  duration_seconds integer NOT NULL CHECK (duration_seconds >= 0),
  buffer_minutes smallint NOT NULL DEFAULT 15 CHECK (buffer_minutes BETWEEN 0 AND 120),
  route_geometry geometry(LineString, 4326), -- simplified Direction polyline
  metric_source varchar(16) NOT NULL CHECK (metric_source IN ('amap', 'estimate', 'mixed')),
  traffic_observed_at timestamptz,
  UNIQUE (day_id, leg_order),
  UNIQUE (from_stop_id, to_stop_id),
  CHECK (from_stop_id <> to_stop_id)
);
CREATE INDEX IF NOT EXISTS itinerary_legs_day_idx ON itinerary_legs(day_id, leg_order);
CREATE INDEX IF NOT EXISTS itinerary_legs_geometry_gix ON itinerary_legs USING gist (route_geometry);

CREATE TABLE IF NOT EXISTS plan_shares (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid NOT NULL REFERENCES itinerary_plans(id) ON DELETE CASCADE,
  token_hash char(64) NOT NULL UNIQUE, -- store HMAC/hash, never a plaintext short-link token
  permission varchar(16) NOT NULL DEFAULT 'view' CHECK (permission IN ('view', 'comment', 'edit')),
  expires_at timestamptz,
  revoked_at timestamptz,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS plan_shares_plan_idx ON plan_shares(plan_id) WHERE revoked_at IS NULL;

-- Optional queue/outbox for asynchronous live-traffic re-plans, PDF exports and webhook events.
CREATE TABLE IF NOT EXISTS planning_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid REFERENCES itinerary_plans(id) ON DELETE CASCADE,
  job_type varchar(32) NOT NULL CHECK (job_type IN ('recalculate', 'export_pdf', 'refresh_poi')),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  status varchar(16) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
  attempts smallint NOT NULL DEFAULT 0,
  available_at timestamptz NOT NULL DEFAULT now(),
  locked_at timestamptz,
  finished_at timestamptz,
  error_code text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS planning_jobs_poll_idx ON planning_jobs(status, available_at) WHERE status = 'queued';

-- Production RLS outline (enable after application sets app.current_user_id per request):
-- ALTER TABLE itinerary_plans ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY plans_owner_policy ON itinerary_plans
--   USING (owner_id = current_setting('app.current_user_id', true)::uuid);
-- Add matching policies to days/stops/legs through plan ownership or expose them only via SECURITY DEFINER views.

COMMIT;
