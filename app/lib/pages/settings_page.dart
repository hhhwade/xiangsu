import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/app_settings.dart';

/// 设置：后端服务器地址 + Bearer token（必须与 deploy/.env 的 API_TOKEN 一致）
class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});
  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  late final TextEditingController _url;
  late final TextEditingController _token;

  @override
  void initState() {
    super.initState();
    final s = context.read<AppSettings>();
    _url = TextEditingController(text: s.baseUrl);
    _token = TextEditingController(text: s.token);
  }

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppSettings>();
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('后端服务', style: TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              TextField(
                controller: _url,
                decoration: const InputDecoration(
                  labelText: '服务器地址',
                  hintText: 'https://your-domain 或 http://IP:8000',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.url,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _token,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: '访问令牌 (API_TOKEN)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () async {
                  await s.save(baseUrl: _url.text, token: _token.text);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('已保存 ✅')));
                  }
                },
                icon: const Icon(Icons.save),
                label: const Text('保存'),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: const Padding(
            padding: EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('说明',
                  style: TextStyle(fontWeight: FontWeight.w700)),
              SizedBox(height: 8),
              Text(
                '• Q 版生成与补发功能由后端 GPU 推理完成\n'
                '• 弱网时大图需要等待几秒，进度条会实时更新\n'
                '• 历史记录里的图片链接默认 7 天有效期\n'
                '• 后端部署与模型下载见工程 docs/部署与打包手册',
                style: TextStyle(fontSize: 13, height: 1.6),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 8),
        const Center(
            child: Text('v1.0.0 · AI 美颜修图',
                style: TextStyle(color: Colors.grey, fontSize: 12))),
      ]),
    );
  }
}
