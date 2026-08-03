import 'package:flutter/material.dart';

/// 主题：奶油白底 + 暖橙强调 + 薄荷绿点缀（圆角卡片，清新可爱暖调）
class AppTheme {
  static const cream = Color(0xFFFFF8F0);   // 奶油白
  static const orange = Color(0xFFFF8A4C);  // 暖橙主色
  static const orangeDeep = Color(0xFFEE6F2E);
  static const mint = Color(0xFF7FDCC3);    // 薄荷绿点缀
  static const ink = Color(0xFF3B3230);

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: cream,
        colorScheme: ColorScheme.fromSeed(
          seedColor: orange,
          primary: orange,
          secondary: mint,
          surface: Colors.white,
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: cream,
          foregroundColor: ink,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
              color: ink, fontSize: 18, fontWeight: FontWeight.w700),
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 2,
          shadowColor: Colors.orange.withValues(alpha: 0.15),
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20)),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: orange,
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16)),
            textStyle:
                const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
        ),
        sliderTheme: SliderThemeData(
          activeTrackColor: orange,
          thumbColor: orangeDeep,
          inactiveTrackColor: mint.withValues(alpha: 0.4),
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.white,
          selectedItemColor: orange,
          unselectedItemColor: Colors.grey,
        ),
      );
}
