import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'app_settings.dart';

class TaskResult {
  final String taskId;
  final String status; // queued | running | done | failed
  final double progress;
  final String? originalUrl;
  final String? resultUrl;
  final String? error;
  final List<String> notices;

  TaskResult({
    required this.taskId,
    required this.status,
    required this.progress,
    this.originalUrl,
    this.resultUrl,
    this.error,
    this.notices = const [],
  });
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

/// 后端 REST 客户端：提交任务 + 轮询进度
class ApiService {
  final AppSettings settings;
  ApiService(this.settings);

  Uri _u(String path) => Uri.parse('${settings.baseUrl}$path');
  Map<String, String> get _headers =>
      {'Authorization': 'Bearer ${settings.token}'};

  /// 提交图片任务（multipart：file + params(JSON)），返回 task_id
  Future<String> submit(
      String endpoint, File image, Map<String, dynamic> params) async {
    final req = http.MultipartRequest('POST', _u(endpoint))
      ..headers.addAll(_headers)
      ..fields['params'] = jsonEncode(params)
      ..files.add(await http.MultipartFile.fromPath('file', image.path));
    http.Response res;
    try {
      res = await http.Response.fromStream(
          await req.send().timeout(const Duration(seconds: 60)));
    } on SocketException {
      throw ApiException('无法连接服务器，请到「设置」检查后端地址与网络');
    }
    if (res.statusCode == 401 || res.statusCode == 403) {
      throw ApiException('鉴权失败：token 与后端 API_TOKEN 不一致');
    }
    if (res.statusCode != 200) {
      throw ApiException('提交失败(${res.statusCode})：${res.body}');
    }
    return jsonDecode(res.body)['task_id'] as String;
  }

  Future<TaskResult> query(String taskId) async {
    final res = await http
        .get(_u('/api/task/$taskId'), headers: _headers)
        .timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) {
      throw ApiException('查询失败(${res.statusCode})：${res.body}');
    }
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    return TaskResult(
      taskId: taskId,
      status: j['status'] as String? ?? 'queued',
      progress: (j['progress'] as num?)?.toDouble() ?? 0,
      originalUrl: j['original_url'] as String?,
      resultUrl: j['result_url'] as String?,
      error: j['error'] as String?,
      notices: (j['notices'] as List?)?.cast<String>() ?? const [],
    );
  }

  /// 提交后轮询直至完成（约 4 分钟超时，后端队列排队时以页面提示为准）
  Stream<TaskResult> submitAndWatch(
      String endpoint, File image, Map<String, dynamic> params) async* {
    final id = await submit(endpoint, image, params);
    var waited = 0;
    while (waited < 480) {
      final r = await query(id);
      yield r;
      if (r.status == 'done' || r.status == 'failed') return;
      await Future<void>.delayed(const Duration(seconds: 1));
      waited++;
    }
    throw ApiException('等待超时：任务仍在排队，请稍后在历史记录查看');
  }
}
