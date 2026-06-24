/// SmartAttend AI — API Endpoint Constants
///
/// baseUrl: Update for your Render deployment URL.
/// All paths must match the FastAPI router prefixes.
class ApiConstants {
  // ── Base URL ─────────────────────────────────────────────────────────────
  // Android emulator: use 10.0.2.2 to reach localhost
  // Physical device: use your machine's local IP or Render URL
  // Production: https://your-app.onrender.com
  static String baseUrl = 'https://smart-attend-ai-20u4.onrender.com';

  // ── Auth ──────────────────────────────────────────────────────────────────
  static const String registerStudent = '/students/register';
  static const String loginStudent    = '/auth/student/login';
  static const String loginFaculty    = '/auth/faculty/login';
  static const String loginAdmin      = '/auth/admin/login';

  // ── Face Registration ─────────────────────────────────────────────────────
  static const String faceRegister = '/face/register';
  static const String faceStatus   = '/face/status';
  static const String faceReset    = '/face/reset';

  // ── Liveness ──────────────────────────────────────────────────────────────
  static const String livenessChallenge = '/liveness/challenge';
  static const String livenessVerify    = '/liveness/verify';

  // ── Attendance ────────────────────────────────────────────────────────────
  static const String attendanceVerify  = '/attendance/verify';
  static const String attendanceHistory = '/attendance/history';
  static String sessionAttendance(int sessionId) => '/attendance/session/$sessionId';

  // ── Faculty ───────────────────────────────────────────────────────────────
  static const String sessionCreate   = '/faculty/session/create';
  static String sessionEnd(int id)    => '/faculty/session/$id/end';
  static const String sessionActive   = '/faculty/session/active';
  static String sessionQR(int id)     => '/faculty/session/$id/qr';
  static String sessionReport(int id) => '/faculty/report/$id';
  static String sessionLive(int id)   => '/faculty/live/$id';
  static const String manualReview    = '/faculty/attendance/review';

  // ── Admin ─────────────────────────────────────────────────────────────────
  static const String adminStudents   = '/admin/students';
  static const String adminFaculty    = '/admin/faculty';
  static const String adminSubjects   = '/admin/subjects';
  static const String adminClassrooms = '/admin/classrooms';
  static const String adminBeacons    = '/admin/beacons';
  static const String adminAnalytics  = '/admin/analytics';

  // ── BLE ───────────────────────────────────────────────────────────────────
  static const String bleBeacons = '/admin/beacons';
}
