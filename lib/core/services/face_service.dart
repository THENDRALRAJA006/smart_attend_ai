import 'package:dio/dio.dart' as dio_pkg;
import 'package:camera/camera.dart';
import 'package:get/get.dart';
import 'api_service.dart';
import '../constants/api_constants.dart';

class FaceService extends GetxService {
  final ApiService _apiService = Get.find<ApiService>();

  Future<Map<String, dynamic>?> registerStudentFace(List<XFile> imageFiles) async {
    try {
      final List<dio_pkg.MultipartFile> filesToUpload = [];
      
      for (XFile file in imageFiles) {
        filesToUpload.add(
          await dio_pkg.MultipartFile.fromFile(
            file.path,
            filename: file.name,
          ),
        );
      }

      final formData = dio_pkg.FormData.fromMap({
        'files': filesToUpload,
      });

      final response = await _apiService.dio.post(
        ApiConstants.faceRegister,
        data: formData,
        options: dio_pkg.Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          sendTimeout: const Duration(minutes: 3), // Face analysis takes longer
          receiveTimeout: const Duration(minutes: 3),
        ),
      );

      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      // Dio interceptor handles displaying error banners
    }
    return null;
  }

  Future<Map<String, dynamic>?> getFaceRegistrationStatus() async {
    try {
      final response = await _apiService.dio.get(ApiConstants.faceStatus);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      // Interceptor handles
    }
    return null;
  }

  Future<bool> resetStudentFace(int studentId) async {
    try {
      final response = await _apiService.dio.delete(
        ApiConstants.faceReset,
        queryParameters: {'student_id': studentId},
      );
      if (response.statusCode == 200) {
        return true;
      }
    } catch (e) {
      // Handled by interceptor
    }
    return false;
  }
}
