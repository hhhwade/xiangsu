import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/app_settings.dart';
import '../theme.dart';
import '../widgets/image_picker_sheet.dart';
import '../widgets/labeled_slider.dart';
import 'result_page.dart';

class _Feature {
  final String key;
  final String label;
  final String desc;
  final bool needSd; // 补发需要后端 SD/GPU 模式
  bool enabled;
  double level;

  _Feature(this.key, this.label, this.desc,
      {this.needSd = false, this.enabled = false, this.level = 0.5});
}

/// 功能二：AI 美颜 P 图 — 子功能勾选 + 各自强度滑块
class BeautifyPage extends StatefulWidget {
  const BeautifyPage({super.key});
  @override
  State<BeautifyPage> createState() => _BeautifyPageState();
}

class _BeautifyPageState extends State<BeautifyPage> {
  File? _image;
  double _ratio = 3 / 4;
  double _progress = 0;
  bool _busy = false;
  Color _hairColor = const Color(0xFF583828); // 默认深棕

  final List<_Feature> _features = [
    _Feature('whiten', '美白', '肤色均匀提亮，不过曝'),
    _Feature('smooth', '磨皮', '去痘印/细纹，保留纹理'),
    _Feature('slim_face', '瘦脸', '两腮/下颌轮廓内收'),
    _Feature('big_eye', '大眼', '虹膜与眼眶放大'),
    _Feature('lip', '唇色', '唇部自然提亮、气色提升'),
    _Feature('brow', '眉形', '眉峰轻抬，更精神'),
    _Feature('slim_body', '瘦身', '腰腹/手臂轮廓内收'),
    _Feature('slim_leg', '瘦腿', '腿部拉长塑形'),
    _Feature('hair_level', '美发', '发色调整 + 光泽增强'),
    _Feature('hair_fill', '补发', '发际线生成填充（需 GPU/SD 模式）', needSd: true),
  ];

  static const List<Color> _hairPresets = [
    Color(0xFF2B1B14), // 自然黑
    Color(0xFF583828), // 深棕
    Color(0xFF8A5A2B), // 栗棕
    Color(0xFFB5651D), // 金棕
    Color(0xFF6B6B7A), // 亚麻灰
  ];

  Future<void> _pick() async {
    final r = await pickImageFlow(context);
    if (r != null) setState(() {
      _image = r.file;
      _ratio = r.aspectRatio;
    });
  }

  Future<void> _run() async {
    if (_image == null || _busy) return;
    final ops = <String, dynamic>{};
    for (final f in _features) {
      if (f.enabled) ops[f.key] = f.level;
    }
    if (ops.isEmpty) {
      _toast('先勾选至少一个子功能～');
      return;
    }
    // 美发需要把颜色也带上（磨皮保留纹理默认值）
    if ((ops['hair_level'] ?? 0) > 0) {
      ops['hair_color'] = [
        (_hairColor.r * 255).round(),
        (_hairColor.g * 255).round(),
        (_hairColor.b * 255).round()
      ];
      ops['hair_gloss'] = 0.3;
    }
    if ((ops['smooth'] ?? 0) > 0) ops['smooth_keep_texture'] = 0.35;

    setState(() {
      _busy = true;
      _progress = 0.05;
    });
    final api = ApiService(context.read<AppSettings>());
    try {
      late TaskResult last;
      await for (final r
          in api.submitAndWatch('/api/beautify', _image!, {'ops': ops})) {
        setState(() => _progress = r.progress);
        last = r;
      }
      if (last.resultUrl != null && mounted) {
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ResultPage(
            type: 'beautify',
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
      appBar: AppBar(title: const Text('AI 美颜 P 图')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
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
                        Text('点我拍照 / 从相册选择',
                            style: TextStyle(color: Colors.grey)),
                      ],
                    )
                  : Image.file(_image!, fit: BoxFit.cover),
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('选择要改善的项（可多选）',
                    style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                ..._features.map(_featureTile),
                if (_features.any((f) => f.key == 'hair_level' && f.enabled))
                  _hairColorRow(),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        _busy
            ? Column(children: [
                LinearProgressIndicator(value: _progress),
                const SizedBox(height: 8),
                Text('AI 修图中… ${(100 * _progress).round()}%',
                    style: TextStyle(color: Colors.grey.shade600)),
              ])
            : ElevatedButton.icon(
                onPressed: _image == null ? null : _run,
                icon: const Icon(Icons.auto_fix_high),
                label: const Text('一键美化'),
              ),
      ]),
    );
  }

  Widget _featureTile(_Feature f) {
    return Column(children: [
      CheckboxListTile(
        contentPadding: EdgeInsets.zero,
        controlAffinity: ListTileControlAffinity.leading,
        title: Row(children: [
          Text(f.label, style: const TextStyle(fontWeight: FontWeight.w600)),
          if (f.needSd)
            Container(
              margin: const EdgeInsets.only(left: 6),
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                  color: AppTheme.mint.withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(6)),
              child: const Text('GPU', style: TextStyle(fontSize: 10)),
            ),
        ]),
        subtitle: Text(f.desc, style: const TextStyle(fontSize: 12)),
        value: f.enabled,
        onChanged: (v) => setState(() => f.enabled = v ?? false),
      ),
      if (f.enabled)
        LabeledSlider(
          label: '强度',
          value: f.level,
          min: 0.05,
          max: 1,
          onChanged: (v) => setState(() => f.level = v),
        ),
    ]);
  }

  Widget _hairColorRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(children: [
        const Text('发色', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(width: 12),
        ..._hairPresets.map((c) => Padding(
              padding: const EdgeInsets.only(right: 8),
              child: InkWell(
                onTap: () => setState(() => _hairColor = c),
                child: Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: c,
                    shape: BoxShape.circle,
                    border: Border.all(
                        width: 3,
                        color: _hairColor == c
                            ? AppTheme.orange
                            : Colors.transparent),
                  ),
                ),
              ),
            )),
      ]),
    );
  }
}
