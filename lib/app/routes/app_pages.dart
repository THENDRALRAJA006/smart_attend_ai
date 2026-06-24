import 'package:get/get.dart';

import '../../features/auth/login_screen.dart';
import '../../features/auth/auth_controller.dart';
import '../../features/registration/face_registration_screen.dart';
import '../../features/registration/face_registration_controller.dart';
import '../../features/attendance/ble_scan_screen.dart';
import '../../features/attendance/liveness_screen.dart';
import '../../features/attendance/selfie_screen.dart';
import '../../features/attendance/attendance_controller.dart';
import '../../features/history/history_screen.dart';
import '../../features/history/history_controller.dart';
import '../../features/faculty/dashboard_screen.dart';
import '../../features/faculty/create_session_screen.dart';
import '../../features/faculty/live_attendance_screen.dart';
import '../../features/faculty/qr_generate_screen.dart';
import '../../features/faculty/faculty_controller.dart';
import '../../features/admin/admin_dashboard_screen.dart';
import '../../features/admin/admin_controller.dart';

part 'app_routes.dart';

class AppPages {
  AppPages._();

  static const INITIAL = Routes.LOGIN;

  static final routes = [
    GetPage(
      name: Routes.LOGIN,
      page: () => const LoginScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<AuthController>(() => AuthController());
      }),
    ),
    GetPage(
      name: Routes.STUDENT_DASHBOARD,
      page: () => const HistoryScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<HistoryController>(() => HistoryController());
      }),
    ),
    GetPage(
      name: Routes.FACE_REGISTRATION,
      page: () => const FaceRegistrationScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<FaceRegistrationController>(() => FaceRegistrationController());
      }),
    ),
    GetPage(
      name: Routes.BLE_SCAN,
      page: () => const BleScanScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<AttendanceController>(() => AttendanceController());
      }),
    ),
    GetPage(
      name: Routes.LIVENESS,
      page: () => const LivenessScreen(),
      // Uses the AttendanceController instance from BLE_SCAN
    ),
    GetPage(
      name: Routes.SELFIE,
      page: () => const SelfieScreen(),
      // Uses the AttendanceController instance
    ),
    GetPage(
      name: Routes.FACULTY_DASHBOARD,
      page: () => const FacultyDashboardScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<FacultyController>(() => FacultyController());
      }),
    ),
    GetPage(
      name: Routes.FACULTY_CREATE_SESSION,
      page: () => const CreateSessionScreen(),
      // Uses the FacultyController instance
    ),
    GetPage(
      name: Routes.FACULTY_LIVE_ATTENDANCE,
      page: () => const LiveAttendanceScreen(),
      // Uses the FacultyController instance
    ),
    GetPage(
      name: Routes.FACULTY_QR_GENERATE,
      page: () => const QrGenerateScreen(),
      // Uses the FacultyController instance
    ),
    GetPage(
      name: Routes.ADMIN_DASHBOARD,
      page: () => const AdminDashboardScreen(),
      binding: BindingsBuilder(() {
        Get.lazyPut<AdminController>(() => AdminController());
      }),
    ),
  ];
}
