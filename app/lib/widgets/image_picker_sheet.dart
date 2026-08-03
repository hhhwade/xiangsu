import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../theme.dart';

class PickResult {
  final File file;
  final double aspectRatio;
  PickResult(this.file, this.aspectRatio);
}

/// 弹出「拍照 / 相册」底部动作菜单 → 选图。
/// 注：为减小编译体积（低内存构建环境），裁剪走「双指放大预览」交互，
///     服务端接收全图；正式版可恢复 image_cropper 插件裁剪。
Future<PickResult?> pickImageFlow(BuildContext context,
    {bool allowCrop = true}) async {
  final source = await showModalBottomSheet<ImageSource>(
    context: context,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
    builder: (ctx) => SafeArea(
      child: Wrap(children: [
        const SizedBox(height: 12),
        const Center(
            child: SizedBox(
                width: 40,
                height: 4,
                child: DecoratedBox(
                    decoration: BoxDecoration(
                        color: Colors.black12,
                        borderRadius:
                            BorderRadius.all(Radius.circular(2)))))),
        ListTile(
          leading: const Icon(Icons.photo_camera, color: AppTheme.orange),
          title: const Text('拍照'),
          onTap: () => Navigator.pop(ctx, ImageSource.camera),
        ),
        ListTile(
          leading: const Icon(Icons.photo_library, color: AppTheme.mint),
          title: const Text('从相册选择'),
          onTap: () => Navigator.pop(ctx, ImageSource.gallery),
        ),
        const SizedBox(height: 8),
      ]),
    ),
  );
  if (source == null) return null;

  final picked = await ImagePicker()
      .pickImage(source: source, maxWidth: 2048, maxHeight: 2048, imageQuality: 95);
  if (picked == null) return null;

  final path = picked.path;
  // 读取实际像素比，用于结果页对比预览
  final bytes = await File(path).readAsBytes();
  final decoded = await decodeImageFromList(bytes);
  final ratio = decoded.width / decoded.height;
  return PickResult(File(path), ratio);
}
