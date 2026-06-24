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
      connectTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
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
        print('--- API REQUEST ---');
        print('Request URL: ${options.uri}');
        print('Request Payload: ${options.data}');
        print('--------------------');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('--- API RESPONSE ---');
        print('Request URL: ${response.requestOptions.uri}');
        print('Response Status: ${response.statusCode}');
        print('Response Body: ${response.data}');
        print('---------------------');
        return handler.next(response);
      },
      onError: (DioException error, handler) async {
        print('--- API ERROR ---');
        print('Request URL: ${error.requestOptions.uri}');
        print('Response Status: ${error.response?.statusCode}');
        print('Error Message: ${error.message}');
        print('Response Body: ${error.response?.data}');
        print('-----------------');
        
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
      final options = BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
      );
      final rawDio = Dio(options);
      
      print('--- API REQUEST (REFRESH) ---');
      print('Request URL: ${ApiConstants.baseUrl}$loginPath');
      print('Request Payload: {"email": $email, "password": "..."}');
      print('-----------------------------');

      final response = await rawDio.post(
        loginPath,
        data: {'email': email, 'password': password},
      );

      print('--- API RESPONSE (REFRESH) ---');
      print('Response Status: ${response.statusCode}');
      print('Response Body: ${response.data}');
      print('------------------------------');

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
