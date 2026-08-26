import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const XingjiTravelApp());
}

/// Android APK shell for the Vue route-planning experience bundled under assets.
/// The embedded build uses the offline planning pool, so it remains usable before a
/// hosted FastAPI endpoint is configured. WebView never needs a localhost service.
class XingjiTravelApp extends StatelessWidget {
  const XingjiTravelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: '行迹智能旅行',
      debugShowCheckedModeBanner: false,
      home: XingjiTravelShell(),
    );
  }
}

class XingjiTravelShell extends StatefulWidget {
  const XingjiTravelShell({super.key});

  @override
  State<XingjiTravelShell> createState() => _XingjiTravelShellState();
}

class _XingjiTravelShellState extends State<XingjiTravelShell> {
  late final WebViewController _controller;
  bool _loading = true;
  WebResourceError? _error;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFFF5F4EF))
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            if (mounted) setState(() => _loading = true);
          },
          onPageFinished: (_) {
            if (mounted) setState(() => _loading = false);
          },
          onWebResourceError: (error) {
            // Only a main-frame failure blocks the bundled application. Optional
            // network resources such as an external font do not replace the UI.
            if (error.isForMainFrame == true && mounted) {
              setState(() {
                _error = error;
                _loading = false;
              });
            }
          },
        ),
      )
      ..loadFlutterAsset('assets/travel_web/index.html');
  }

  Future<bool> _handleBack() async {
    if (await _controller.canGoBack()) {
      await _controller.goBack();
      return false;
    }
    return true;
  }

  Future<void> _retry() async {
    setState(() {
      _error = null;
      _loading = true;
    });
    await _controller.loadFlutterAsset('assets/travel_web/index.html');
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _handleBack,
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F4EF),
        body: SafeArea(
          top: false,
          bottom: false,
          child: Stack(
            fit: StackFit.expand,
            children: [
              WebViewWidget(controller: _controller),
              if (_loading && _error == null)
                const _TravelSplash(),
              if (_error != null)
                _TravelLoadError(
                  message: _error!.description,
                  onRetry: _retry,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TravelSplash extends StatelessWidget {
  const _TravelSplash();

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: const Color(0xFFF5F4EF),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 54,
              height: 54,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: const Color(0xFF143031),
                borderRadius: BorderRadius.circular(17),
              ),
              child: const Text(
                '行',
                style: TextStyle(
                  color: Color(0xFFE6B080),
                  fontSize: 27,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: 15),
            const Text(
              '行迹 · 智能旅行路线',
              style: TextStyle(
                color: Color(0xFF244444),
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Color(0xFFD46F3F),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TravelLoadError extends StatelessWidget {
  const _TravelLoadError({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: const Color(0xFFF5F4EF),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.map_outlined, size: 42, color: Color(0xFFD46F3F)),
              const SizedBox(height: 14),
              const Text(
                '行程页面暂时没有加载完成',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                message.isEmpty ? '请检查应用资源后重试。' : message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF75847F), fontSize: 12),
              ),
              const SizedBox(height: 18),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('重新加载'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
