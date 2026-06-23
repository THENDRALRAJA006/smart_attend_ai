part of 'app_pages.dart';

abstract class Routes {
  Routes._();
  
  static const LOGIN = '/login';
  static const STUDENT_DASHBOARD = '/student-dashboard';
  static const FACE_REGISTRATION = '/face-registration';
  static const BLE_SCAN = '/ble-scan';
  static const LIVENESS = '/liveness';
  static const SELFIE = '/selfie';
  static const FACULTY_DASHBOARD = '/faculty-dashboard';
  static const FACULTY_CREATE_SESSION = '/faculty-create-session';
  static const FACULTY_LIVE_ATTENDANCE = '/faculty-live-attendance';
  static const FACULTY_QR_GENERATE = '/faculty-qr-generate';
  static const ADMIN_DASHBOARD = '/admin-dashboard';
}
