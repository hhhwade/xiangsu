import 'dart:convert';
import 'dart:io';

import 'package:gal/gal.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 历史记录（本地 JSON）+ 保存到相册 + 分享导出
class HistoryEntry {
  final String id;
  final String type; // qstyle | beautify
  final String originalUrl;
  final String resultUrl;
  final DateTime time;

  HistoryEntry({
    required this.id,
    required this.type,
    required this.originalUrl,
    required this.resultUrl,
    required this.time,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type,
        'original_url': originalUrl,
        'result_url': resultUrl,
        'time': time.toIso8601String(),
      };

  factory HistoryEntry.fromJson(Map<String, dynamic> j) => HistoryEntry(
        id: j['id'] as String,
        type: j['type'] as String,
        originalUrl: j['original_url'] as String,
        resultUrl: j['result_url'] as String,
        time: DateTime.parse(j['time'] as String),
      );
}

class Repository {
  static const _kHistory = 'history_v1';
  static final Repository instance = Repository._();
  Repository._();

  Future<void> addHistory(HistoryEntry e) async {
    final p = await SharedPreferences.getInstance();
    final list = (p.getStringList(_kHistory) ?? [])
      ..insert(0, jsonEncode(e.toJson()));
    if (list.length > 100) list.removeRange(100, list.length);
    await p.setStringList(_kHistory, list);
  }

  Future<List<HistoryEntry>> loadHistory() async {
    final p = await SharedPreferences.getInstance();
    final raw = p.getStringList(_kHistory) ?? [];
    return raw
        .map((s) => HistoryEntry.fromJson(jsonDecode(s)))
        .toList(growable: false);
  }

  Future<void> clearHistory() async {
    final p = await SharedPreferences.getInstance();
    await p.remove(_kHistory);
  }

  /// 下载结果图 → 写临时文件（分享）/ 存相册
  Future<File> downloadToTemp(String url, {String prefix = 'res'}) async {
    final bytes = (await http.get(Uri.parse(url))).bodyBytes;
    final dir = await getTemporaryDirectory();
    final name =
        '${prefix}_${DateFormat('yyyyMMdd_HHmmss').format(DateTime.now())}.png';
    final f = File('${dir.path}/$name');
    await f.writeAsBytes(bytes, flush: true);
    return f;
  }

  Future<void> saveToGallery(String url) async {
    if (!await Gal.hasAccess()) {
      final ok = await Gal.requestAccess();
      if (!ok) throw Exception('相册权限被拒绝');
    }
    final bytes = (await http.get(Uri.parse(url))).bodyBytes;
    await Gal.putImageBytes(bytes, album: 'AI美颜');
  }
}
