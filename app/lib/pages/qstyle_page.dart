import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/app_settings.dart';
import '../widgets/image_picker_sheet.dart';
import '../widgets/labeled_slider.dart';
import 'result_page.dart';

/// 功能一：Q 版像素可爱风 — 选图 + 参数滑块 + 生成
class QStylePage extends StatefulWidget {
  const QStylePage({super.key});
  @override
  State<QStylePage> createState() => _QStylePageState();
}

class _QStylePageState extends State<QStylePage> {
  File? _image;
  double _ratio = 3 / 4;
  double _pixel = 12;     // 像素颗粒度（块大小）
  double _strength = 0.55; // Q 化强度
  bool _keepBg = false;   // 保留背景
  double _progress = 0;
  bool _busy = false;

  Future<void> _pick() async {
    final r = await pickImageFlow(context);
    if (r != null) setState(() {
      _image = r.file;
      _ratio = r.aspectRatio;
    });
  }

  Future<void> _run() async {
    if (_image == null || _busy) return;
    setState(() {
      _busy = true;
      _progress = 0.05;
    });
    final api = ApiService(context.read<AppSettings>());
    try {
      late TaskResult last;
      await for (final r in api.submitAndWatch('/api/qstyle', _image!, {
        'pixel_size': _pixel.round(),
        'strength': _strength,
        'keep_bg': _keepBg,
        'mode': 'auto',
      })) {
        setState(() => _progress = r.progress);
        last = r;
      }
      if (last.resultUrl != null && mounted) {
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ResultPage(
            type: 'qstyle',
            originalPath: _image!.path,
            originalUrl: last.originalUrl,
            resultUrl: last.resultUrl!,
            aspectRatio: _ratio,
            notices: last.notices,
          ),
        ));
      }
    } on ApiException catch (e) {
      _toast(e.message);
    } catch (e) {
      _toast('出错了：$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _toast(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Q 版像素风')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        // 图片区
        InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: _pick,
          child: AspectRatio(
            aspectRatio: _image == null ? 1 : _ratio,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.orange.shade100),
              ),
              clipBehavior: Clip.antiAlias,
              child: _image == null
                  ? const Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.add_photo_alternate,
                            size: 48, color: Colors.orange),
                        SizedBox(height: 8),
                        Text('点我拍照 / 从相册选择', style: TextStyle(color: Colors.grey)),
                      ],
                    )
                  : Image.file(_image!, fit: BoxFit.cover),
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 参数卡片
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: Column(children: [
              LabeledSlider(
                label: '像素颗粒度（块大小）',
                value: _pixel.toDouble(),
                min: 4,
                max: 48,
                display: _pixel.round().toString(),
                onChanged: (v) => setState(() => _pixel = v),
              ),
              LabeledSlider(
                label: 'Q 化强度',
                value: _strength,
                min: 0.2,
                max: 0.9,
                onChanged: (v) => setState(() => _strength = v),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('保留原背景'),
                subtitle: const Text('只把主体变 Q 版，背景保持原图',
                    style: TextStyle(fontSize: 12)),
                value: _keepBg,
                onChanged: (v) => setState(() => _keepBg = v),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 16),

        _busy
            ? Column(children: [
                LinearProgressIndicator(value: _progress),
                const SizedBox(height: 8),
                Text('AI 生成中… ${(100 * _progress).round()}%',
                    style: TextStyle(color: Colors.grey.shade600)),
              ])
            : ElevatedButton.icon(
                onPressed: _image == null ? null : _run,
                icon: const Icon(Icons.auto_awesome),
                label: const Text('开始生成'),
              ),
      ]),
    );
  }
}
