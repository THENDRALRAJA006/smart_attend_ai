import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart' as dio_pkg;
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/api_constants.dart';
import '../../core/services/auth_service.dart';

class FacultyController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final AuthService authService = Get.find<AuthService>();

  final RxBool isLoading = false.obs;
  
  // Selection Lists
  final RxList subjects = [].obs;
  final RxList classrooms = [].obs;
  
  // Session States
  final RxMap activeSession = {}.obs;
  final RxBool hasActiveSession = false.obs;

  // QR States
  final RxString qrToken = ''.obs;
  final RxInt qrTimeLeft = 0.obs;
  Timer? _qrTimer;

  // Live Attendance States
  final RxList liveLogs = [].obs;
  final RxInt presentCount = 0.obs;
  StreamSubscription? _sseSubscription;

  @override
  void onInit() {
    super.onInit();
    _loadMetadata();
    checkActiveSession();
  }

  Future<void> _loadMetadata() async {
    try {
      final resSub = await _apiService.dio.get(ApiConstants.adminSubjects);
      if (resSub.statusCode == 200) {
        subjects.value = resSub.data;
      }

      final resCls = await _apiService.dio.get(ApiConstants.adminClassrooms);
      if (resCls.statusCode == 200) {
        classrooms.value = resCls.data;
      }
    } catch (e) {
      // API service interceptor alerts errors
    }
  }

  Future<void> checkActiveSession() async {
    isLoading.value = true;
    try {
      final response = await _apiService.dio.get(ApiConstants.sessionActive);
      if (response.statusCode == 200) {
        activeSession.value = response.data;
        hasActiveSession.value = true;
        
        // Start streaming logs for active session
        startLiveSSEStream(activeSession['id']);
      }
    } catch (e) {
      hasActiveSession.value = false;
      activeSession.clear();
      stopLiveSSEStream();
    }
    isLoading.value = false;
  }

  Future<void> createSession(int subjectId, int classroomId) async {
    isLoading.value = true;
    try {
      final response = await _apiService.dio.post(
        ApiConstants.sessionCreate,
        data: {
          'subject_id': subjectId,
          'classroom_id': classroomId,
        },
      );

      if (response.statusCode == 200) {
        activeSession.value = response.data;
        hasActiveSession.value = true;
        Get.back(); // close create screen
        Get.snackbar('Session Created', 'Class attendance session opened successfully.');
        
        startLiveSSEStream(activeSession['id']);
      }
    } catch (e) {
      // Handled by interceptor
    }
    isLoading.value = false;
  }

  Future<void> endSession() async {
    if (!hasActiveSession.value) return;

    isLoading.value = true;
    try {
      final response = await _apiService.dio.post(
        ApiConstants.sessionEnd(activeSession['id']),
      );

      if (response.statusCode == 200) {
        hasActiveSession.value = false;
        activeSession.clear();
        stopLiveSSEStream();
        liveLogs.clear();
        presentCount.value = 0;
        Get.snackbar('Session Terminated', 'Attendance window closed.');
      }
    } catch (e) {
      // Handled
    }
    isLoading.value = false;
  }

  Future<void> generateQRToken() async {
    if (!hasActiveSession.value) return;

    try {
      final response = await _apiService.dio.post(
        ApiConstants.sessionQR(activeSession['id']),
      );

      if (response.statusCode == 200) {
        qrToken.value = response.data['qr_token'];
        final expiresAt = DateTime.parse(response.data['expires_at']);
        
        // Setup a local ticker countdown
        _qrTimer?.cancel();
        final diff = expiresAt.difference(DateTime.now().toUtc()).inSeconds;
        qrTimeLeft.value = diff > 0 ? diff : 60;

        _qrTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
          if (qrTimeLeft.value > 1) {
            qrTimeLeft.value--;
          } else {
            timer.cancel();
            // Automatically fetch a fresh QR token
            generateQRToken();
          }
        });
      }
    } catch (e) {
      // Handled
    }
  }

  void startLiveSSEStream(int sessionId) async {
    stopLiveSSEStream();
    liveLogs.clear();
    presentCount.value = 0;

    try {
      final response = await _apiService.dio.get(
        ApiConstants.sessionLive(sessionId),
        options: dio_pkg.Options(responseType: dio_pkg.ResponseType.stream),
      );

      final Stream<List<int>> stream = response.data.data;
      _sseSubscription = stream
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) {
        if (line.startsWith('data: ')) {
          final dataJson = line.substring(6).trim();
          if (dataJson.isNotEmpty) {
            try {
              final Map<String, dynamic> log = json.decode(dataJson);
              
              // Add to list and sort (most recent first)
              final index = liveLogs.indexWhere((l) => l['id'] == log['id']);
              if (index != -1) {
                liveLogs[index] = log;
              } else {
                liveLogs.insert(0, log);
              }
              
              // Recount present students
              presentCount.value = liveLogs.where((l) => l['status'] == 'present').length;
            } catch (e) {
              // Parse error
            }
          }
        }
      });
    } catch (e) {
      // Fallback polling if streaming is blocked by middleware or proxy
      _startFallbackPolling(sessionId);
    }
  }

  void _startFallbackPolling(int sessionId) {
    // Fallback polling helper every 5 seconds
    _qrTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      if (!hasActiveSession.value) {
        timer.cancel();
        return;
      }
      try {
        final response = await _apiService.dio.get(ApiConstants.sessionLive(sessionId));
        if (response.statusCode == 200) {
          liveLogs.value = response.data;
          presentCount.value = liveLogs.where((l) => l['status'] == 'present').length;
        }
      } catch (e) {
        // quiet fail
      }
    });
  }

  void stopLiveSSEStream() {
    _sseSubscription?.cancel();
    _sseSubscription = null;
    _qrTimer?.cancel();
  }

  Future<void> reviewOverride(int attendanceId, bool approve) async {
    try {
      final response = await _apiService.dio.post(
        ApiConstants.manualReview,
        data: {
          'attendance_id': attendanceId,
          'approve': approve,
        },
      );

      if (response.statusCode == 200) {
        // Update local status
        final index = liveLogs.indexWhere((l) => l['id'] == attendanceId);
        if (index != -1) {
          liveLogs[index]['status'] = approve ? 'present' : 'rejected';
          liveLogs.refresh();
          
          presentCount.value = liveLogs.where((l) => l['status'] == 'present').length;
        }
        Get.snackbar('Override Success', 'Attendance record status updated.');
      }
    } catch (e) {
      // Handled
    }
  }

  Future<void> downloadCSVReport() async {
    if (!hasActiveSession.value) return;
    try {
      final response = await _apiService.dio.get(
        ApiConstants.sessionReport(activeSession['id']),
        options: dio_pkg.Options(responseType: dio_pkg.ResponseType.bytes),
      );
      
      if (response.statusCode == 200) {
        Get.snackbar(
          'Report Exported',
          'CSV file fetched successfully (${response.data.length} bytes).',
          backgroundColor: Colors.green.withOpacity(0.2),
        );
      }
    } catch (e) {
      // Handled
    }
  }

  @override
  void onClose() {
    stopLiveSSEStream();
    super.onClose();
  }
}
