import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get/get.dart' as getx;
import '../constants/api_constants.dart';

class ApiService extends getx.GetxService {
  late final Dio dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<ApiService> init() async {
    dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Accept': 'application/json',
      },
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'jwt_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException error, handler) async {
        // Handle 401 Token Refresh
        if (error.response?.statusCode == 401) {
          final success = await _attemptTokenRefresh();
          if (success) {
            // Retry the request with the new token
            final requestOptions = error.requestOptions;
            final newToken = await _storage.read(key: 'jwt_token');
            requestOptions.headers['Authorization'] = 'Bearer $newToken';
            
            // Re-execute request
            try {
              final response = await dio.fetch(requestOptions);
              return handler.resolve(response);
            } catch (e) {
              return handler.next(error);
            }
          } else {
            // Logout and redirect to login page
            await _storage.delete(key: 'jwt_token');
            getx.Get.offAllNamed('/login');
            getx.Get.snackbar(
              'Session Expired',
              'Your session has expired. Please login again.',
              snackPosition: getx.SnackPosition.BOTTOM,
            );
          }
        } else {
          // General Network Error Banner
          String errorMsg = 'An unexpected network error occurred.';
          if (error.type == DioExceptionType.connectionTimeout) {
            errorMsg = 'Connection timed out. Please check your internet connection.';
          } else if (error.response != null) {
            final data = error.response?.data;
            if (data is Map && data.containsKey('detail')) {
              errorMsg = data['detail'];
            }
          }
          getx.Get.snackbar(
            'Error',
            errorMsg,
            snackPosition: getx.SnackPosition.BOTTOM,
            backgroundColor: getx.Get.theme.colorScheme.errorContainer,
            colorText: getx.Get.theme.colorScheme.onErrorContainer,
          );
        }
        return handler.next(error);
      },
    ));

    return this;
  }

  Future<bool> _attemptTokenRefresh() async {
    final email = await _storage.read(key: 'user_email');
    final password = await _storage.read(key: 'user_password');
    final role = await _storage.read(key: 'user_role');

    if (email == null || password == null || role == null) {
      return false;
    }

    try {
      String loginPath = '';
      if (role == 'student') {
        loginPath = ApiConstants.loginStudent;
      } else if (role == 'faculty') {
        loginPath = ApiConstants.loginFaculty;
      } else if (role == 'admin') {
        loginPath = ApiConstants.loginAdmin;
      }

      // We make a raw request bypassing interceptors to avoid loops
      final response = await Dio(BaseOptions(baseUrl: ApiConstants.baseUrl)).post(
        loginPath,
        data: {'email': email, 'password': password},
      );

      if (response.statusCode == 200) {
        final token = response.data['token']['access_token'];
        await _storage.write(key: 'jwt_token', value: token);
        return true;
      }
    } catch (e) {
      // Refresh login failed
      return false;
    }
    return false;
  }
}
