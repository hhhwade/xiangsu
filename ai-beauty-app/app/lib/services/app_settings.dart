import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 全局设置：后端地址 + 鉴权 token（设置页可改，持久化）
class AppSettings extends ChangeNotifier {
  static const _kBaseUrl = 'base_url';
  static const _kToken = 'token';

  /// ⚠️ 首次打开 APP 需到「设置」页改成你自己的服务器地址
  String baseUrl = 'http://YOUR_SERVER_IP:8000';
  String token = 'please-change-this-to-a-long-random-string';

  Future<void> load() async {
    final p = await SharedPreferences.getInstance();
    baseUrl = p.getString(_kBaseUrl) ?? baseUrl;
    token = p.getString(_kToken) ?? token;
    notifyListeners();
  }

  Future<void> save({String? baseUrl, String? token}) async {
    final p = await SharedPreferences.getInstance();
    if (baseUrl != null) await p.setString(_kBaseUrl, baseUrl.trim());
    if (token != null) await p.setString(_kToken, token.trim());
    if (baseUrl != null) this.baseUrl = baseUrl.trim();
    if (token != null) this.token = token.trim();
    notifyListeners();
  }
}
