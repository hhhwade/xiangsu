package com.xingji.travel;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

import com.amap.api.maps.AMap;
import com.amap.api.maps.CameraUpdateFactory;
import com.amap.api.maps.MapView;
import com.amap.api.maps.MapsInitializer;
import com.amap.api.maps.model.BitmapDescriptorFactory;
import com.amap.api.maps.model.LatLng;
import com.amap.api.maps.model.LatLngBounds;
import com.amap.api.maps.model.MarkerOptions;
import com.amap.api.maps.model.PolylineOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

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

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            MapsInitializer.initialize(getApplicationContext());
        } catch (Exception ignored) {
            // The SDK will surface an auth/network state in the map view when available.
        }

        LinearLayout root = new LinearLayout(this);
        // Portrait stacked layout: route planner scrolls above, native AMap stays
        // visible below. This avoids squeezing the route panel into a narrow column.
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245, 244, 239));

        webView = createPlannerWebView();
        mapView = new MapView(this);
        mapView.onCreate(state);
        amap = mapView.getMap();
        amap.getUiSettings().setZoomControlsEnabled(true);
        amap.getUiSettings().setCompassEnabled(false);

        root.addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 0.56f));
        FrameLayout mapFrame = new FrameLayout(this);
        mapFrame.addView(mapView, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(mapFrame, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 0.44f));
        setContentView(root);
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
    }

    private void renderRoute(String payload) {
        if (amap == null || payload == null || payload.isEmpty()) return;
        try {
            JSONObject body = new JSONObject(payload);
            String transportMode = body.optString("transportMode", "driving");
            JSONArray routes = body.optJSONArray("routes");
            if (routes == null) return;
            amap.clear();
            LatLngBounds.Builder bounds = LatLngBounds.builder();
            boolean hasPoint = false;

            for (int routeIndex = 0; routeIndex < routes.length(); routeIndex++) {
                JSONObject route = routes.optJSONObject(routeIndex);
                if (route == null) continue;
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
                    int day = route.optInt("day", 1);
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
                    PolylineOptions line = new PolylineOptions()
                        .addAll(points)
                        .width(width)
                        .color(color)
                        .zIndex(5f);
                    // Public transit is visually distinct; the JS route generator also
                    // changes stop order and segment durations for every transport mode.
                    if ("transit".equals(transportMode)) line.setDottedLine(true);
                    amap.addPolyline(line);
                }
            }
            if (hasPoint) {
                amap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds.build(), (int) dp(42)));
            }
        } catch (Exception ignored) {
            // Invalid bridge data should never break the native map or the route list.
        }
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
