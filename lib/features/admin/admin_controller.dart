import 'package:get/get.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/api_constants.dart';
import '../../core/services/auth_service.dart';

class AdminController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final AuthService authService = Get.find<AuthService>();

  final RxBool isLoading = false.obs;

  // Analytics Metrics
  final RxInt totalStudents = 0.obs;
  final RxInt totalFaculty = 0.obs;
  final RxInt totalSubjects = 0.obs;
  final RxInt totalClassrooms = 0.obs;
  final RxInt activeSessionsCount = 0.obs;
  final RxDouble attendanceRate = 0.0.obs;

  // CRUD Lists
  final RxList studentsList = [].obs;
  final RxList facultyList = [].obs;
  final RxList subjectsList = [].obs;
  final RxList classroomsList = [].obs;
  final RxList beaconsList = [].obs;

  @override
  void onInit() {
    super.onInit();
    refreshAdminData();
  }

  Future<void> refreshAdminData() async {
    isLoading.value = true;
    await Future.wait([
      fetchAnalytics(),
      loadStudents(),
      loadFaculty(),
      loadSubjects(),
      loadClassrooms(),
      loadBeacons(),
    ]);
    isLoading.value = false;
  }

  Future<void> fetchAnalytics() async {
    try {
      final response = await _apiService.dio.get(ApiConstants.adminAnalytics);
      if (response.statusCode == 200) {
        final data = response.data;
        totalStudents.value = data['total_students'] ?? 0;
        totalFaculty.value = data['total_faculty'] ?? 0;
        totalSubjects.value = data['total_subjects'] ?? 0;
        totalClassrooms.value = data['total_classrooms'] ?? 0;
        activeSessionsCount.value = data['active_sessions'] ?? 0;
        attendanceRate.value = (data['attendance_rate'] as num?)?.toDouble() ?? 0.0;
      }
    } catch (e) {
      // Handled
    }
  }

  // --- Students CRUD API ---
  Future<void> loadStudents() async {
    final response = await _apiService.dio.get(ApiConstants.adminStudents);
    if (response.statusCode == 200) studentsList.value = response.data;
  }

  Future<void> addStudent(Map<String, dynamic> data) async {
    final response = await _apiService.dio.post(ApiConstants.adminStudents, data: data);
    if (response.statusCode == 201) {
      loadStudents();
      fetchAnalytics();
      Get.snackbar('Student Added', 'New student registered successfully.');
    }
  }

  Future<void> deleteStudent(int id) async {
    final response = await _apiService.dio.delete('${ApiConstants.adminStudents}/$id');
    if (response.statusCode == 200) {
      loadStudents();
      fetchAnalytics();
      Get.snackbar('Student Removed', 'Student record deleted.');
    }
  }

  // --- Faculty CRUD API ---
  Future<void> loadFaculty() async {
    final response = await _apiService.dio.get(ApiConstants.adminFaculty);
    if (response.statusCode == 200) facultyList.value = response.data;
  }

  Future<void> addFaculty(Map<String, dynamic> data) async {
    final response = await _apiService.dio.post(ApiConstants.adminFaculty, data: data);
    if (response.statusCode == 201) {
      loadFaculty();
      fetchAnalytics();
      Get.snackbar('Faculty Added', 'New faculty registered successfully.');
    }
  }

  Future<void> deleteFaculty(int id) async {
    final response = await _apiService.dio.delete('${ApiConstants.adminFaculty}/$id');
    if (response.statusCode == 200) {
      loadFaculty();
      fetchAnalytics();
      Get.snackbar('Faculty Removed', 'Faculty record deleted.');
    }
  }

  // --- Subjects CRUD API ---
  Future<void> loadSubjects() async {
    final response = await _apiService.dio.get(ApiConstants.adminSubjects);
    if (response.statusCode == 200) subjectsList.value = response.data;
  }

  Future<void> addSubject(Map<String, dynamic> data) async {
    final response = await _apiService.dio.post(ApiConstants.adminSubjects, data: data);
    if (response.statusCode == 201) {
      loadSubjects();
      fetchAnalytics();
      Get.snackbar('Subject Created', 'New course curriculum added.');
    }
  }

  Future<void> deleteSubject(int id) async {
    final response = await _apiService.dio.delete('${ApiConstants.adminSubjects}/$id');
    if (response.statusCode == 200) {
      loadSubjects();
      fetchAnalytics();
      Get.snackbar('Subject Removed', 'Subject record deleted.');
    }
  }

  // --- Classrooms CRUD API ---
  Future<void> loadClassrooms() async {
    final response = await _apiService.dio.get(ApiConstants.adminClassrooms);
    if (response.statusCode == 200) classroomsList.value = response.data;
  }

  Future<void> addClassroom(Map<String, dynamic> data) async {
    final response = await _apiService.dio.post(ApiConstants.adminClassrooms, data: data);
    if (response.statusCode == 201) {
      loadClassrooms();
      fetchAnalytics();
      Get.snackbar('Classroom Created', 'New physical classroom room registered.');
    }
  }

  Future<void> deleteClassroom(int id) async {
    final response = await _apiService.dio.delete('${ApiConstants.adminClassrooms}/$id');
    if (response.statusCode == 200) {
      loadClassrooms();
      fetchAnalytics();
      Get.snackbar('Classroom Removed', 'Classroom room profile deleted.');
    }
  }

  // --- Beacons CRUD API ---
  Future<void> loadBeacons() async {
    final response = await _apiService.dio.get(ApiConstants.adminBeacons);
    if (response.statusCode == 200) beaconsList.value = response.data;
  }

  Future<void> addBeacon(Map<String, dynamic> data) async {
    final response = await _apiService.dio.post(ApiConstants.adminBeacons, data: data);
    if (response.statusCode == 201) {
      loadBeacons();
      Get.snackbar('Beacon Registered', 'New BLE hardware beacon linked.');
    }
  }

  Future<void> deleteBeacon(int id) async {
    final response = await _apiService.dio.delete('${ApiConstants.adminBeacons}/$id');
    if (response.statusCode == 200) {
      loadBeacons();
      Get.snackbar('Beacon Removed', 'BLE beacon deleted.');
    }
  }
}
