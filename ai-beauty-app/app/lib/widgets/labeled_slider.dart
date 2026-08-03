import 'package:flutter/material.dart';

/// 标签 + 值 + 滑杆（参数微调统一控件）
class LabeledSlider extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final ValueChanged<double> onChanged;
  final String? display;

  const LabeledSlider({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.min = 0,
    this.max = 1,
    this.display,
  });

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
        const Spacer(),
        Text(display ?? value.toStringAsFixed(2),
            style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
      ]),
      Slider(value: value, min: min, max: max, onChanged: onChanged),
    ]);
  }
}
