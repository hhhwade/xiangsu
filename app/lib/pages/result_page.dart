import 'dart:io';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../services/repository.dart';
import '../theme.dart';
import '../widgets/before_after_slider.dart';

/// 结果页：前后对比滑块 + 保存相册 + 分享 + 写入历史
class ResultPage extends StatefulWidget {
  final String type; // qstyle | beautify
  final String originalPath; // 本地原图（对比更准确）
  final String? originalUrl;
  final String resultUrl;
  final double aspectRatio;
  final List<String> notices;

  const ResultPage({
    super.key,
    required this.type,
    required this.originalPath,
    this.originalUrl,
    required this.resultUrl,
    required this.aspectRatio,
    this.notices = const [],
  });

  @override
  State<ResultPage> createState() => _ResultPageState();
}

class _ResultPageState extends State<ResultPage> {
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    // 自动写入历史记录（展示用网络缩略图；URL 有过期时间，过期后会重新走生成流程）
    Repository.instance.addHistory(HistoryEntry(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: widget.type,
      originalUrl: widget.originalUrl ?? '',
      resultUrl: widget.resultUrl,
      time: DateTime.now(),
    ));
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await Repository.instance.saveToGallery(widget.resultUrl);
      _toast('已保存到相册 ❤️');
    } catch (e) {
      _toast('保存失败：$e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _share() async {
    try {
      final f = await Repository.instance.downloadToTemp(widget.resultUrl);
      await Share.shareXFiles([XFile(f.path)], text: 'AI 美颜修图一下～');
    } catch (e) {
      _toast('分享失败：$e');
    }
  }

  void _toast(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.type == 'qstyle' ? '你的 Q 版形象' : '修图完成')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        BeforeAfterSlider(
          before: FileImage(File(widget.originalPath)),
          after: NetworkImage(widget.resultUrl),
          aspectRatio: widget.aspectRatio,
        ),
        if (widget.notices.isNotEmpty) ...[
          const SizedBox(height: 12),
          ...widget.notices.map((n) => Text('⚠️ $n',
              style: TextStyle(color: Colors.orange.shade800, fontSize: 12))),
        ],
        const SizedBox(height: 20),
        Row(children: [
          Expanded(
            child: OutlinedButton.icon(
              onPressed: _saving ? null : _save,
              icon: const Icon(Icons.download, color: AppTheme.orange),
              label: _saving
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('保存相册',
                      style: TextStyle(color: AppTheme.orange)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppTheme.orange),
                minimumSize: const Size.fromHeight(52),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: ElevatedButton.icon(
              onPressed: _share,
              icon: const Icon(Icons.share),
              label: const Text('分享'),
            ),
          ),
        ]),
      ]),
    );
  }
}
