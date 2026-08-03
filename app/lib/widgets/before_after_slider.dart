import 'package:flutter/material.dart';

import '../theme.dart';

/// 前后对比拖动滑块：左边是「修图后」，右边是「原图」，中间分割线可拖动
class BeforeAfterSlider extends StatefulWidget {
  final ImageProvider before; // 原图
  final ImageProvider after;  // 成品图
  final double aspectRatio;   // 预览宽高比（默认 3/4）

  const BeforeAfterSlider({
    super.key,
    required this.before,
    required this.after,
    this.aspectRatio = 3 / 4,
  });

  @override
  State<BeforeAfterSlider> createState() => _BeforeAfterSliderState();
}

class _BeforeAfterSliderState extends State<BeforeAfterSlider> {
  double _pos = 0.5;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: widget.aspectRatio,
      child: LayoutBuilder(builder: (context, c) {
        final w = c.maxWidth;
        return GestureDetector(
          onHorizontalDragUpdate: (d) =>
              setState(() => _pos = (_pos + d.delta.dx / w).clamp(0.02, 0.98)),
          onTapDown: (d) =>
              setState(() => _pos = (d.localPosition.dx / w).clamp(0.02, 0.98)),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: Stack(fit: StackFit.expand, children: [
              // 底层：原图
              Image(image: widget.before, fit: BoxFit.cover),
              // 上层左侧：成品图（按 _pos 裁剪可见宽度）
              ClipRect(
                child: Align(
                  alignment: Alignment.centerLeft,
                  widthFactor: _pos,
                  child: SizedBox(
                      width: w,
                      child:
                          Image(image: widget.after, fit: BoxFit.cover)),
                ),
              ),
              _tag('原图', Alignment.centerRight, AppTheme.mint),
              _tag('效果图', Alignment.centerLeft, AppTheme.orange),
              // 分割竖线 + 手柄
              Positioned(
                left: w * _pos - 1,
                top: 0,
                bottom: 0,
                child: Container(width: 2, color: Colors.white),
              ),
              Positioned(
                left: w * _pos - 17,
                top: c.maxHeight / 2 - 17,
                child: Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                          color: Colors.black.withValues(alpha: 0.2),
                          blurRadius: 6)
                    ],
                  ),
                  child: const Icon(Icons.compare_arrows,
                      color: AppTheme.orange, size: 20),
                ),
              ),
            ]),
          ),
        );
      }),
    );
  }

  Widget _tag(String text, Alignment align, Color color) => IgnorePointer(
        child: Align(
          alignment: align,
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(30)),
              child: Text(text,
                  style: const TextStyle(color: Colors.white, fontSize: 12)),
            ),
          ),
        ),
      );
}
