import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../services/repository.dart';

/// 历史记录：本地保存任务结果 URL（MinIO 预签 URL，默认 7 天有效）
class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});
  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  late Future<List<HistoryEntry>> _future;

  @override
  void initState() {
    super.initState();
    _future = Repository.instance.loadHistory();
  }

  Future<void> _reload() async {
    setState(() => _future = Repository.instance.loadHistory());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('历史记录'), actions: [
        IconButton(
          icon: const Icon(Icons.delete_sweep),
          onPressed: () async {
            await Repository.instance.clearHistory();
            _reload();
          },
        ),
      ]),
      body: FutureBuilder<List<HistoryEntry>>(
        future: _future,
        builder: (ctx, snap) {
          final list = snap.data ?? [];
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (list.isEmpty) {
            return const Center(child: Text('还没有记录，去试试吧～'));
          }
          return RefreshIndicator(
            onRefresh: _reload,
            child: GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12),
              itemCount: list.length,
              itemBuilder: (ctx, i) {
                final e = list[i];
                return Card(
                  clipBehavior: Clip.antiAlias,
                  child: InkWell(
                    onTap: () {
                      // 点按放大查看（网络预览）
                      showDialog(
                        context: ctx,
                        builder: (_) => Dialog(
                          insetPadding: const EdgeInsets.all(16),
                          child: InteractiveViewer(
                            child: Image.network(
                                e.resultUrl,
                                fit: BoxFit.contain,
                                loadingBuilder: (_, child, p) => p == null
                                    ? child
                                    : const SizedBox(
                                        width: 300,
                                        height: 300,
                                        child: Center(
                                            child:
                                                CircularProgressIndicator())),
                                errorBuilder: (_, __, ___) => const Padding(
                                    padding: EdgeInsets.all(24),
                                    child: Text(
                                        '图片 URL 已过期（默认 7 天），请重新生成'))),
                          ),
                        ),
                      );
                    },
                    child: Column(children: [
                      Expanded(
                        child: Image.network(
                          e.resultUrl,
                          fit: BoxFit.cover,
                          width: double.infinity,
                          loadingBuilder: (_, child, p) => p == null
                              ? child
                              : Container(
                                  color: Colors.orange.shade50,
                                  child: const Center(
                                      child: CircularProgressIndicator())),
                          errorBuilder: (_, __, ___) => Container(
                              color: Colors.orange.shade50,
                              child: const Icon(Icons.broken_image)),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(8),
                        child: Row(children: [
                          Chip(
                            label: Text(
                                e.type == 'qstyle' ? 'Q版' : '美颜',
                                style: const TextStyle(fontSize: 10)),
                            visualDensity: VisualDensity.compact,
                          ),
                          const Spacer(),
                          Text(DateFormat('MM-dd HH:mm').format(e.time),
                              style: TextStyle(
                                  fontSize: 11, color: Colors.grey.shade500)),
                        ]),
                      ),
                    ]),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
