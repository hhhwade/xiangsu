package com.xingji.travel;

import android.app.Activity;
import android.graphics.Color;
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
import com.amap.api.maps.model.LatLng;
import com.amap.api.maps.model.LatLngBounds;
import com.amap.api.maps.model.MarkerOptions;
import com.amap.api.maps.model.PolylineOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Native Android AMap host for the landscape two-pane travel planner.
 *
 * The Vue route list lives in the left WebView. It calls XingjiNativeMap.updateRoute
 * whenever the selected day, generated plan, or drag order changes; this native
 * MapView on the right then renders real AMap markers and coloured route polylines.
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
        root.setOrientation(LinearLayout.HORIZONTAL);
        root.setBackgroundColor(Color.rgb(245, 244, 239));

        webView = createPlannerWebView();
        mapView = new MapView(this);
        mapView.onCreate(state);
        amap = mapView.getMap();
        amap.getUiSettings().setZoomControlsEnabled(true);
        amap.getUiSettings().setCompassEnabled(false);

        root.addView(webView, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 0.40f));
        FrameLayout mapFrame = new FrameLayout(this);
        mapFrame.addView(mapView, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(mapFrame, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 0.60f));
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
                    amap.addMarker(new MarkerOptions()
                        .position(point)
                        .title((spotIndex + 1) + ". " + name)
                        .snippet(arrival.isEmpty() ? route.optString("title", "智能路线") : "到达 " + arrival)
                        .zIndex(10f + spotIndex));
                }
                if (points.size() > 1) {
                    amap.addPolyline(new PolylineOptions()
                        .addAll(points)
                        .width(dp(6))
                        .color(color)
                        .zIndex(5f));
                }
            }
            if (hasPoint) {
                amap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds.build(), (int) dp(42)));
            }
        } catch (Exception ignored) {
            // Invalid bridge data should never break the native map or the route list.
        }
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
