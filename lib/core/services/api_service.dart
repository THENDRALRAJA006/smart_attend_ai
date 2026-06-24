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
        print('API Request: ${options.uri}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('API Response: $response');
        return handler.next(response);
      },
      onError: (DioException error, handler) async {
        print('API Request: ${error.requestOptions.uri}');
        print('API Response: ${error.response}');
        
        final statusCode = error.response?.statusCode;
        
        // Handle 401 Token Refresh
        if (statusCode == 401) {
          final success = await _attemptTokenRefresh();
          if (success) {
            final requestOptions = error.requestOptions;
            final newToken = await _storage.read(key: 'jwt_token');
            requestOptions.headers['Authorization'] = 'Bearer $newToken';
            try {
              final response = await dio.fetch(requestOptions);
              return handler.resolve(response);
            } catch (e) {
              return handler.next(error);
            }
          } else {
            await _storage.delete(key: 'jwt_token');
            getx.Get.offAllNamed('/login');
            getx.Get.snackbar(
              'Session Expired',
              'Your session has expired. Please login again.',
              snackPosition: getx.SnackPosition.BOTTOM,
            );
            return handler.next(error);
          }
        }

        // Do not show error banners for 404 (Not Found) if it's checking active states
        final path = error.requestOptions.path;
        if (statusCode == 404 && path.contains('/session/active')) {
          return handler.next(error);
        }

        String errorMsg = 'An unexpected error occurred.';
        
        if (error.type == DioExceptionType.connectionTimeout ||
            error.type == DioExceptionType.sendTimeout ||
            error.type == DioExceptionType.receiveTimeout) {
          errorMsg = 'Network timeout: Connection timed out. Please check your internet connection.';
        } else if (error.type == DioExceptionType.connectionError) {
          errorMsg = 'Backend unavailable: Cannot connect to the server. Please check if the backend is running.';
        } else if (error.type == DioExceptionType.badResponse) {
          if (statusCode == 400) {
            errorMsg = 'Bad Request (400): ';
            final data = error.response?.data;
            if (data is Map && data.containsKey('detail')) {
              errorMsg += data['detail'];
            } else {
              errorMsg += 'Invalid input request.';
            }
          } else if (statusCode == 403) {
            errorMsg = 'Forbidden (403): Access denied. You do not have permission.';
          } else if (statusCode == 404) {
            errorMsg = 'Not Found (404): The requested resource was not found.';
          } else if (statusCode == 500) {
            errorMsg = 'Internal Server Error (500): The server encountered an error processing your request.';
          } else {
            errorMsg = 'Error ($statusCode): ${error.response?.statusMessage ?? 'Bad response received.'}';
          }
        } else {
          errorMsg = 'Backend unavailable: The server did not respond or returned an invalid response.';
        }

        getx.Get.snackbar(
          'API Error',
          errorMsg,
          snackPosition: getx.SnackPosition.BOTTOM,
          backgroundColor: getx.Get.theme.colorScheme.errorContainer,
          colorText: getx.Get.theme.colorScheme.onErrorContainer,
          duration: const Duration(seconds: 4),
        );

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
