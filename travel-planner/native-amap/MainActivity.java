package com.xingji.travel;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.amap.api.maps.AMap;
import com.amap.api.maps.CameraUpdateFactory;
import com.amap.api.maps.MapView;
import com.amap.api.maps.MapsInitializer;
import com.amap.api.maps.model.BitmapDescriptorFactory;
import com.amap.api.maps.model.LatLng;
import com.amap.api.maps.model.LatLngBounds;
import com.amap.api.maps.model.MarkerOptions;
import com.amap.api.maps.model.PolylineOptions;
import com.amap.api.services.core.LatLonPoint;
import com.amap.api.services.core.PoiItem;
import com.amap.api.services.poisearch.Photo;
import com.amap.api.services.poisearch.PoiResult;
import com.amap.api.services.poisearch.PoiSearch;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Native Android AMap host for the portrait stacked travel planner.
 *
 * The scrollable route panel lives above the map. It calls XingjiNativeMap.updateRoute
 * whenever the selected day, generated plan, transport mode, or drag order changes;
 * the native MapView below then renders real AMap markers and coloured route polylines.
 */
public final class MainActivity extends Activity {
    private MapView mapView;
    private AMap amap;
    private WebView webView;
    private TextView mapRouteCaption;
    private long lastRouteRevision = -1L;
    private int poiRequestSerial = 0;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            MapsInitializer.setProtocol(MapsInitializer.HTTPS);
            MapsInitializer.initialize(getApplicationContext());
        } catch (Exception ignored) {
            // The SDK will surface an auth/network state in the map view when available.
        }

        LinearLayout root = new LinearLayout(this);
        // Portrait stacked layout: route planner scrolls above, native AMap stays
        // visible below. This avoids squeezing the route panel into a narrow column.
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245, 244, 239));

        // Construct the map before loading the WebView. This removes a startup race
        // where a first route payload could arrive before MapView was ready.
        mapView = new MapView(this);
        mapView.onCreate(state);
        amap = mapView.getMap();
        amap.getUiSettings().setZoomControlsEnabled(true);
        amap.getUiSettings().setCompassEnabled(false);
        webView = createPlannerWebView();

        root.addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 0.62f));
        View divider = new View(this);
        divider.setBackgroundColor(Color.rgb(218, 227, 218));
        root.addView(divider, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (int) dp(3)));
        FrameLayout mapFrame = new FrameLayout(this);
        mapFrame.addView(mapView, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        mapRouteCaption = createMapRouteCaption();
        FrameLayout.LayoutParams captionParams = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        captionParams.leftMargin = (int) dp(10);
        captionParams.topMargin = (int) dp(10);
        mapFrame.addView(mapRouteCaption, captionParams);
        root.addView(mapFrame, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 0.38f));
        setContentView(root);
    }

    private TextView createMapRouteCaption() {
        TextView caption = new TextView(this);
        caption.setText("高德地图 · 等待路线同步");
        caption.setTextColor(Color.rgb(38, 79, 72));
        caption.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        caption.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        caption.setPadding((int) dp(9), (int) dp(6), (int) dp(9), (int) dp(6));
        GradientDrawable background = new GradientDrawable();
        background.setColor(Color.argb(238, 255, 255, 252));
        background.setCornerRadius(dp(8));
        background.setStroke((int) dp(1), Color.rgb(214, 226, 216));
        caption.setBackground(background);
        return caption;
    }

    private WebView createPlannerWebView() {
        WebView view = new WebView(this);
        view.setBackgroundColor(Color.WHITE);
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setDomStorageEnabled(true);
        view.getSettings().setAllowFileAccess(true);
        view.addJavascriptInterface(new RouteBridge(), "XingjiNativeMap");
        view.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView browser, String url) {
                super.onPageFinished(browser, url);
                // Keep only the planner/list panel in the WebView; its map column is
                // replaced by the native AMap MapView in the adjacent Android pane.
                browser.evaluateJavascript(
                    "document.documentElement.classList.add('native-amap-split');",
                    null
                );
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView browser, WebResourceRequest request) {
                return false;
            }
        });
        view.loadUrl("file:///android_asset/www/index.html");
        return view;
    }

    private final class RouteBridge {
        @JavascriptInterface
        public void updateRoute(final String payload) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    renderRoute(payload);
                }
            });
        }

        @JavascriptInterface
        public void focusSpot(final double latitude, final double longitude) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (amap != null) {
                        amap.animateCamera(CameraUpdateFactory.newLatLngZoom(new LatLng(latitude, longitude), 15f));
                    }
                }
            });
        }

        /** Request real AMap POIs for the entered national city without exposing a Web Service key. */
        @JavascriptInterface
        public void searchPois(final String city, final String keywords) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    requestAmapPois(city, keywords);
                }
            });
        }
    }

    private void requestAmapPois(final String city, String keywords) {
        if (city == null || city.trim().isEmpty()) return;
        try {
            final int requestId = ++poiRequestSerial;
            String[] rawTerms = (keywords == null || keywords.trim().isEmpty() ? "旅游景点" : keywords).split("\\|");
            final ArrayList<String> terms = new ArrayList<>();
            for (String raw : rawTerms) {
                if (raw != null && !raw.trim().isEmpty() && !terms.contains(raw.trim())) terms.add(raw.trim());
            }
            if (terms.isEmpty()) terms.add("旅游景点");

            final Map<String, JSONObject> merged = new LinkedHashMap<>();
            final int[] finished = {0};
            final int total = terms.size();
            for (String term : terms) {
                PoiSearch.Query query = new PoiSearch.Query(term, "", city.trim());
                query.setCityLimit(true);
                query.setPageSize(20);
                PoiSearch search = new PoiSearch(this, query);
                search.setOnPoiSearchListener(new PoiSearch.OnPoiSearchListener() {
                    @Override
                    public void onPoiSearched(PoiResult result, int code) {
                        if (requestId != poiRequestSerial) return;
                        if (code == 1000 && result != null && result.getPois() != null) {
                            for (PoiItem item : result.getPois()) appendPoi(city, item, merged);
                        }
                        finished[0]++;
                        if (finished[0] >= total) {
                            JSONArray pois = new JSONArray();
                            for (JSONObject poi : merged.values()) pois.put(poi);
                            dispatchNativePois(city, pois, pois.length() > 0 ? 1000 : code);
                        }
                    }

                    @Override
                    public void onPoiItemSearched(PoiItem item, int code) {
                        // Route planning consumes list search results only.
                    }
                });
                search.searchPOIAsyn();
            }
        } catch (Exception error) {
            dispatchNativePois(city, new JSONArray(), -1);
        }
    }

    private void appendPoi(String city, PoiItem item, Map<String, JSONObject> merged) {
        if (item == null || item.getLatLonPoint() == null) return;
        try {
            LatLonPoint point = item.getLatLonPoint();
            String id = emptyTo(item.getPoiId(), item.getTitle() + "@" + point.getLatitude() + "," + point.getLongitude());
            if (merged.containsKey(id)) return;
            String type = emptyTo(item.getTypeDes(), "高德推荐景点");
            String address = emptyTo(item.getSnippet(), "高德 POI 实时返回地点");
            String imageUrl = "";
            if (item.getPhotos() != null && !item.getPhotos().isEmpty()) {
                Photo firstPhoto = item.getPhotos().get(0);
                if (firstPhoto != null && firstPhoto.getUrl() != null) imageUrl = firstPhoto.getUrl();
            }
            JSONObject poi = new JSONObject();
            poi.put("id", id);
            poi.put("name", item.getTitle());
            poi.put("type", type);
            poi.put("lng", point.getLongitude());
            poi.put("lat", point.getLatitude());
            poi.put("address", address);
            poi.put("imageUrl", imageUrl);
            poi.put("overview", buildPoiOverview(city, item.getTitle(), type));
            merged.put(id, poi);
        } catch (Exception ignored) {
            // Skip malformed POI records but keep the rest of the live result set.
        }
    }

    private String emptyTo(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }

    /** A concise landmark overview, distinct from the address/snippet returned by AMap. */
    private String buildPoiOverview(String city, String name, String type) {
        String category = emptyTo(type, "特色景点");
        String theme;
        if (category.contains("博物馆") || category.contains("展览")) {
            theme = "以当地历史、艺术或专题内容为核心的文化参观地点";
        } else if (category.contains("风景") || category.contains("公园") || category.contains("山") || category.contains("湖")) {
            theme = "以自然景观、步行观赏和城市休闲体验为主的地点";
        } else if (category.contains("寺") || category.contains("宗教")) {
            theme = "兼具宗教文化与建筑观赏价值的静谧人文空间";
        } else if (category.contains("餐") || category.contains("美食")) {
            theme = "集中体验当地饮食和市井氛围的风味节点";
        } else if (category.contains("购物") || category.contains("商场")) {
            theme = "融合购物、餐饮和休闲功能的城市活力区域";
        } else {
            theme = "具有当地城市特色和游览价值的代表性地点";
        }
        return name + "是" + city + "的" + category + "，" + theme + "。";
    }

    private void dispatchNativePois(String city, JSONArray pois, int code) {
        try {
            JSONObject payload = new JSONObject();
            payload.put("city", city);
            payload.put("code", code);
            payload.put("pois", pois);
            final String escaped = JSONObject.quote(payload.toString());
            if (webView != null) {
                webView.post(new Runnable() {
                    @Override public void run() {
                        webView.evaluateJavascript("window.XingjiNativePoiResult && window.XingjiNativePoiResult(" + escaped + ");", null);
                    }
                });
            }
        } catch (Exception ignored) {
            // Offline city route fallback stays available.
        }
    }

    private void renderRoute(String payload) {
        if (amap == null || payload == null || payload.isEmpty()) return;
        try {
            JSONObject body = new JSONObject(payload);
            long revision = body.optLong("revision", lastRouteRevision + 1L);
            // WebView callbacks can be queued while a user changes day/mode quickly.
            // Never repaint an older route over a newer selection.
            if (revision < lastRouteRevision) return;
            lastRouteRevision = revision;
            String transportMode = body.optString("transportMode", "driving");
            JSONArray routes = body.optJSONArray("routes");
            if (routes == null) return;
            amap.clear();
            LatLngBounds.Builder bounds = LatLngBounds.builder();
            boolean hasPoint = false;

            for (int routeIndex = 0; routeIndex < routes.length(); routeIndex++) {
                JSONObject route = routes.optJSONObject(routeIndex);
                if (route == null) continue;
                int day = route.optInt("day", 1);
                if (mapRouteCaption != null) {
                    mapRouteCaption.setText("Day " + day + " · " + route.optString("title", "经典路线") + " · " + transportLabel(transportMode) + " · 编号已同步");
                }
                int color = Color.parseColor(route.optString("color", "#D46F3F"));
                JSONArray spots = route.optJSONArray("spots");
                if (spots == null || spots.length() == 0) continue;

                List<LatLng> points = new ArrayList<>();
                for (int spotIndex = 0; spotIndex < spots.length(); spotIndex++) {
                    JSONObject spot = spots.optJSONObject(spotIndex);
                    if (spot == null) continue;
                    JSONObject location = spot.optJSONObject("location");
                    if (location == null) continue;
                    double latitude = location.optDouble("lat", Double.NaN);
                    double longitude = location.optDouble("lng", Double.NaN);
                    if (Double.isNaN(latitude) || Double.isNaN(longitude)) continue;
                    LatLng point = new LatLng(latitude, longitude);
                    points.add(point);
                    bounds.include(point);
                    hasPoint = true;
                    String name = spot.optString("name", "景点");
                    String arrival = spot.optString("arrivalTime", "");
                    // The visible number is intentionally the same index as the
                    // corresponding route card above the map: no guesswork between
                    // the classic route list and the AMap marker order.
                    amap.addMarker(new MarkerOptions()
                        .position(point)
                        .icon(numberedMarker(spotIndex + 1, color))
                        .anchor(0.5f, 0.5f)
                        .title("Day " + day + " · " + (spotIndex + 1) + ". " + name)
                        .snippet(arrival.isEmpty() ? route.optString("title", "智能路线") : "第 " + (spotIndex + 1) + " 站 · " + arrival + " 到达")
                        .zIndex(10f + spotIndex));
                }
                if (points.size() > 1) {
                    float width = dp("driving".equals(transportMode) ? 9 : "riding".equals(transportMode) ? 7 : 6);
                    // Draw each segment separately and add a directional arrow in its
                    // midpoint. Together with numbered markers this makes the exact
                    // 1 → 2 → 3 order visually unambiguous on the native map.
                    for (int segment = 0; segment < points.size() - 1; segment++) {
                        LatLng from = points.get(segment);
                        LatLng to = points.get(segment + 1);
                        PolylineOptions line = new PolylineOptions()
                            .add(from, to)
                            .width(width)
                            .color(color)
                            .zIndex(5f);
                        if ("transit".equals(transportMode)) line.setDottedLine(true);
                        amap.addPolyline(line);
                        LatLng midpoint = new LatLng((from.latitude + to.latitude) / 2d, (from.longitude + to.longitude) / 2d);
                        amap.addMarker(new MarkerOptions()
                            .position(midpoint)
                            .icon(routeArrow(color))
                            .anchor(0.5f, 0.5f)
                            .rotateAngle(bearing(from, to))
                            .zIndex(7f));
                    }
                }
            }
            if (hasPoint) {
                amap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds.build(), (int) dp(42)));
            }
        } catch (Exception ignored) {
            // Invalid bridge data should never break the native map or the route list.
        }
    }

    private String transportLabel(String mode) {
        if ("walking".equals(mode)) return "步行";
        if ("riding".equals(mode)) return "骑行";
        if ("transit".equals(mode)) return "公交";
        return "自驾";
    }

    private com.amap.api.maps.model.BitmapDescriptor routeArrow(int color) {
        int size = Math.max(16, (int) dp(18));
        Bitmap bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setColor(Color.WHITE);
        Path border = new Path();
        border.moveTo(size * 0.18f, size * 0.12f);
        border.lineTo(size * 0.88f, size * 0.5f);
        border.lineTo(size * 0.18f, size * 0.88f);
        border.close();
        canvas.drawPath(border, paint);
        paint.setColor(color);
        Path arrow = new Path();
        arrow.moveTo(size * 0.26f, size * 0.22f);
        arrow.lineTo(size * 0.78f, size * 0.5f);
        arrow.lineTo(size * 0.26f, size * 0.78f);
        arrow.close();
        canvas.drawPath(arrow, paint);
        return BitmapDescriptorFactory.fromBitmap(bitmap);
    }

    private float bearing(LatLng from, LatLng to) {
        double fromLat = Math.toRadians(from.latitude);
        double toLat = Math.toRadians(to.latitude);
        double deltaLng = Math.toRadians(to.longitude - from.longitude);
        double y = Math.sin(deltaLng) * Math.cos(toLat);
        double x = Math.cos(fromLat) * Math.sin(toLat) - Math.sin(fromLat) * Math.cos(toLat) * Math.cos(deltaLng);
        return (float) ((Math.toDegrees(Math.atan2(y, x)) + 360d) % 360d);
    }

    /** Draw a numbered, route-coloured marker so map order stays visibly aligned with cards. */
    private com.amap.api.maps.model.BitmapDescriptor numberedMarker(int order, int color) {
        int size = Math.max(28, (int) dp(34));
        Bitmap bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setColor(Color.WHITE);
        canvas.drawCircle(size / 2f, size / 2f, size / 2f, paint);
        paint.setColor(color);
        canvas.drawCircle(size / 2f, size / 2f, size / 2f - Math.max(2, dp(2)), paint);
        paint.setColor(Color.WHITE);
        paint.setTextAlign(Paint.Align.CENTER);
        paint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        paint.setTextSize(Math.max(11, dp(order > 9 ? 11 : 13)));
        Paint.FontMetrics metrics = paint.getFontMetrics();
        float baseline = size / 2f - (metrics.ascent + metrics.descent) / 2f;
        canvas.drawText(String.valueOf(order), size / 2f, baseline, paint);
        return BitmapDescriptorFactory.fromBitmap(bitmap);
    }

    private float dp(int value) {
        return TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, value, getResources().getDisplayMetrics());
    }

    @Override protected void onResume() { super.onResume(); if (mapView != null) mapView.onResume(); }
    @Override protected void onPause() { if (mapView != null) mapView.onPause(); super.onPause(); }
    @Override protected void onDestroy() { if (mapView != null) mapView.onDestroy(); super.onDestroy(); }
    @Override public void onLowMemory() { super.onLowMemory(); if (mapView != null) mapView.onLowMemory(); }
    @Override protected void onSaveInstanceState(Bundle outState) { super.onSaveInstanceState(outState); if (mapView != null) mapView.onSaveInstanceState(outState); }
}
