import 'package:dio/dio.dart' as dio_pkg;
import 'package:camera/camera.dart';
import 'package:get/get.dart';
import 'api_service.dart';
import '../constants/api_constants.dart';

class LivenessChallengeResult {
  final String token;
  final String challenge;
  final DateTime expiresAt;

  LivenessChallengeResult({
    required this.token,
    required this.challenge,
    required this.expiresAt,
  });

  factory LivenessChallengeResult.fromJson(Map<String, dynamic> json) {
    return LivenessChallengeResult(
      token: json['token'],
      challenge: json['challenge'],
      expiresAt: DateTime.parse(json['expires_at']),
    );
  }
}

class LivenessVerifyResult {
  final bool verified;
  final String? livenessToken;
  final String message;

  LivenessVerifyResult({
    required this.verified,
    this.livenessToken,
    required this.message,
  });

  factory LivenessVerifyResult.fromJson(Map<String, dynamic> json) {
    return LivenessVerifyResult(
      verified: json['verified'],
      livenessToken: json['liveness_token'],
      message: json['message'] ?? '',
    );
  }
}

class LivenessService extends GetxService {
  final ApiService _apiService = Get.find<ApiService>();

  Future<LivenessChallengeResult?> fetchChallenge() async {
    try {
      final response = await _apiService.dio.post(ApiConstants.livenessChallenge);
      if (response.statusCode == 200) {
        return LivenessChallengeResult.fromJson(response.data);
      }
    } catch (e) {
      // Handled by interceptor
    }
    return null;
  }

  Future<LivenessVerifyResult?> verifyChallenge({
    required String challengeToken,
    required List<XFile> frameFiles,
  }) async {
    try {
      final List<dio_pkg.MultipartFile> multipartFrames = [];
      
      for (XFile f in frameFiles) {
        multipartFrames.add(
          await dio_pkg.MultipartFile.fromFile(
            f.path,
            filename: f.name,
          ),
        );
      }

      final formData = dio_pkg.FormData.fromMap({
        'token': challengeToken,
        'files': multipartFrames,
      });

      final response = await _apiService.dio.post(
        ApiConstants.livenessVerify,
        data: formData,
        options: dio_pkg.Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      if (response.statusCode == 200) {
        return LivenessVerifyResult.fromJson(response.data);
      }
    } catch (e) {
      // Interceptor handles
    }
    return null;
  }
}
