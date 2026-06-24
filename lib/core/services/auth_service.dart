import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get/get.dart';
import 'api_service.dart';
import '../constants/api_constants.dart';
import '../../app/routes/app_pages.dart';

class AuthService extends GetxService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final ApiService _apiService = Get.find<ApiService>();

  final RxBool isLoggedIn = false.obs;
  final RxString userRole = ''.obs;
  final RxMap currentUser = {}.obs;

  Future<AuthService> init() async {
    final token = await _storage.read(key: 'jwt_token');
    final role = await _storage.read(key: 'user_role');
    final name = await _storage.read(key: 'user_name');
    final email = await _storage.read(key: 'user_email');
    final id = await _storage.read(key: 'user_id');

    if (token != null && role != null) {
      isLoggedIn.value = true;
      userRole.value = role;
      currentUser.value = {
        'id': id,
        'name': name,
        'email': email,
        'role': role,
      };
    }
    return this;
  }

  Future<bool> login({
    required String email,
    required String password,
    required String role,
  }) async {
    try {
      String endpoint = '';
      if (role == 'student') {
        endpoint = ApiConstants.loginStudent;
      } else if (role == 'faculty') {
        endpoint = ApiConstants.loginFaculty;
      } else if (role == 'admin') {
        endpoint = ApiConstants.loginAdmin;
      }

      final response = await _apiService.dio.post(endpoint, data: {
        'email': email,
        'password': password,
      });

      if (response.statusCode == 200) {
        final data = response.data;
        final token = data['token']['access_token'];
        final user = data['user'];

        // Save credentials and details in Secure Storage
        await _storage.write(key: 'jwt_token', value: token);
        await _storage.write(key: 'user_role', value: role);
        await _storage.write(key: 'user_email', value: email);
        await _storage.write(key: 'user_password', value: password);
        await _storage.write(key: 'user_name', value: user['name'] ?? '');
        await _storage.write(key: 'user_id', value: user['id'].toString());

        userRole.value = role;
        currentUser.value = {
          'id': user['id'].toString(),
          'name': user['name'] ?? '',
          'email': email,
          'role': role,
        };
        isLoggedIn.value = true;
        return true;
      }
    } catch (e) {
      // Dio error handler in interceptor handles snackbar alerts
    }
    return false;
  }

  Future<bool> registerStudent({
    required String name,
    required String rollNo,
    required String email,
    required String password,
    required String department,
    required int year,
    required String section,
  }) async {
    try {
      final response = await _apiService.dio.post(ApiConstants.registerStudent, data: {
        'full_name': name,
        'roll_number': rollNo,
        'email': email,
        'password': password,
        'department': department,
        'year': year,
        'section': section,
      });

      if (response.statusCode == 201) {
        final data = response.data;
        final token = data['token']['access_token'];
        final user = data['user'];

        await _storage.write(key: 'jwt_token', value: token);
        await _storage.write(key: 'user_role', value: 'student');
        await _storage.write(key: 'user_email', value: email);
        await _storage.write(key: 'user_password', value: password);
        await _storage.write(key: 'user_name', value: user['name'] ?? '');
        await _storage.write(key: 'user_id', value: user['id'].toString());

        userRole.value = 'student';
        currentUser.value = {
          'id': user['id'].toString(),
          'name': user['name'] ?? '',
          'email': email,
          'role': 'student',
        };
        isLoggedIn.value = true;
        return true;
      }
    } catch (e) {
      // Handled by Dio error interceptor
    }
    return false;
  }

  Future<void> logout() async {
    await _storage.deleteAll();
    isLoggedIn.value = false;
    userRole.value = '';
    currentUser.clear();
    Get.offAllNamed(Routes.LOGIN);
  }
}
