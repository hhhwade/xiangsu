import 'package:flutter/material.dart';

import '../theme.dart';
import 'beautify_page.dart';
import 'qstyle_page.dart';

/// 首页：两个大入口（Q 版像素风 / AI 美颜 P 图）
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI 美颜修图 ✨')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          const SizedBox(height: 8),
          _entry(
            context,
            title: 'Q 版像素风',
            subtitle: '人像 / 宠物 / 风景 → 大眼圆脸像素小可爱',
            icon: Icons.grid_on,
            color: AppTheme.orange,
            page: const QStylePage(),
          ),
          const SizedBox(height: 16),
          _entry(
            context,
            title: 'AI 美颜 P 图',
            subtitle: '美白·磨皮·美发·补发·瘦脸·瘦身·瘦腿，一键专业修图',
            icon: Icons.face_retouching_natural,
            color: AppTheme.mint,
            page: const BeautifyPage(),
          ),
          const Spacer(),
          Text('提示：首次使用请到「设置」配置后端服务器',
              style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
          const SizedBox(height: 12),
        ]),
      ),
    );
  }

  Widget _entry(BuildContext context,
      {required String title,
      required String subtitle,
      required IconData icon,
      required Color color,
      required Widget page}) {
    return InkWell(
      borderRadius: BorderRadius.circular(24),
      onTap: () =>
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => page)),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Row(children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Icon(icon, color: color, size: 34),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text(subtitle,
                    style:
                        TextStyle(color: Colors.grey.shade600, fontSize: 13)),
              ]),
            ),
            Icon(Icons.chevron_right, color: Colors.grey.shade400),
          ]),
        ),
      ),
    );
  }
}
