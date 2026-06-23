import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'app/routes/app_pages.dart';
import 'core/services/api_service.dart';
import 'core/services/auth_service.dart';
import 'core/services/ble_service.dart';
import 'core/services/face_service.dart';
import 'core/services/liveness_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Core Services sequentially
  await Get.putAsync(() => ApiService().init());
  await Get.putAsync(() => AuthService().init());
  
  Get.put(BleService());
  Get.put(FaceService());
  Get.put(LivenessService());

  runApp(const SmartAttendApp());
}

class SmartAttendApp extends StatelessWidget {
  const SmartAttendApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'SmartAttend AI',
      debugShowCheckedModeBanner: false,
      
      // Stunning Premium Dark Theme System
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6C63FF),
          brightness: Brightness.dark,
          primary: const Color(0xFF6C63FF),
          secondary: const Color(0xFF00D2FF),
          surface: const Color(0xFF161722),
          error: const Color(0xFFFF4A75),
        ),
        scaffoldBackgroundColor: const Color(0xFF0D0E15),
        
        // Custom Typography
        textTheme: const TextTheme(
          headlineLarge: TextStyle(fontSize: 32.0, fontWeight: FontWeight.bold, letterSpacing: -0.5),
          headlineMedium: TextStyle(fontSize: 24.0, fontWeight: FontWeight.w600),
          titleLarge: TextStyle(fontSize: 20.0, fontWeight: FontWeight.w600),
          bodyLarge: TextStyle(fontSize: 16.0, color: Color(0xFFE2E8F0)),
          bodyMedium: TextStyle(fontSize: 14.0, color: Color(0xFF94A3B8)),
        ),
        
        // Card styling
        cardTheme: const CardThemeData(
          color: Color(0xFF161722),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(16.0),
              topRight: Radius.circular(16.0),
              bottomLeft: Radius.circular(16.0),
              bottomRight: Radius.circular(16.0),
            ),
            side: BorderSide(color: Color(0xFF232533), width: 1),
          ),
        ),
        
        // Input theme
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF1E202E),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: const BorderSide(color: Color(0xFF6C63FF), width: 1.5),
          ),
          labelStyle: const TextStyle(color: Color(0xFF94A3B8)),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),

        // Button theme
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF6C63FF),
            foregroundColor: Colors.white,
            elevation: 0,
            minimumSize: const Size(double.infinity, 54),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12.0),
            ),
            textStyle: const TextStyle(
              fontSize: 16.0,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ),
      ),
      initialRoute: AppPages.INITIAL,
      getPages: AppPages.routes,
    );
  }
}
