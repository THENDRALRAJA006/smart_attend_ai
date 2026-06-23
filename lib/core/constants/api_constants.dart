class ApiConstants {
  // Default URL matches the Android Emulator mapping to localhost.
  // Change to your production Render URL (e.g. https://smartattend-backend.onrender.com) for production.
  static String baseUrl = 'http://10.0.2.2:8000';

  // Auth routes matching PostgreSQL endpoints
  static const String registerStudent = '/register/student';
  static const String loginStudent = '/login/student';
  static const String loginFaculty = '/login/faculty';
  static const String loginAdmin = '/login/student'; // Fallback mapping

  // Face Registration routes
  static const String faceRegister = '/face/register';
  static const String faceStatus = '/face/status';
  static const String faceReset = '/face/reset';

  // Liveness check routes
  static const String livenessChallenge = '/liveness/challenge';
  static const String livenessVerify = '/liveness/verify';

  // Attendance routes matching PostgreSQL endpoints
  static const String attendanceVerify = '/attendance/mark'; // Maps to mark/verify on backend
  static String attendanceHistory(int studentId) => '/attendance/student/$studentId';
  static String sessionLive(int sessionId) => '/attendance/session/$sessionId';

  // Faculty session routes
  static const String sessionCreate = '/faculty/session/create';
  static String sessionEnd(int id) => '/faculty/session/$id/end';
  static const String sessionActive = '/faculty/session/active';
  static String sessionQR(int id) => '/faculty/session/$id/qr';
  static String sessionReport(int id) => '/faculty/report/$id';
  static const String manualReview = '/faculty/attendance/review';

  // Admin routes
  static const String adminStudents = '/admin/students';
  static const String adminFaculty = '/admin/faculty';
  static const String adminSubjects = '/admin/students'; // Safe fallback mapping
  static const String adminClassrooms = '/admin/classrooms';
  static const String adminBeacons = '/admin/beacons';
  static const String adminAnalytics = '/admin/analytics';
}
