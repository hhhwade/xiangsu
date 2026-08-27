import 'package:xingji_travel_app/theme.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('主题色符合设计（奶油白/暖橙/薄荷绿）', () {
    expect(AppTheme.cream.value, 0xFFFFF8F0);
    expect(AppTheme.orange.value, 0xFFFF8A4C);
    expect(AppTheme.mint.value, 0xFF7FDCC3);
  });
}
