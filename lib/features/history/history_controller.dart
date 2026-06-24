import 'package:get/get.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/api_constants.dart';

/// Model representing a single attendance record in the history list
class AttendanceHistoryRecord {
  final int id;
  final int sessionId;
  final String attendanceStatus;
  final bool livenessVerified;
  final double? similarityScore;
  final DateTime markedAt;

  AttendanceHistoryRecord({
    required this.id,
    required this.sessionId,
    required this.attendanceStatus,
    required this.livenessVerified,
    this.similarityScore,
    required this.markedAt,
  });

  factory AttendanceHistoryRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceHistoryRecord(
      id: json['id'] ?? 0,
      sessionId: json['session_id'] ?? 0,
      attendanceStatus: json['attendance_status'] ?? 'unknown',
      livenessVerified: json['liveness_verified'] ?? false,
      similarityScore: json['similarity_score']?.toDouble(),
      markedAt: json['marked_at'] != null
          ? DateTime.tryParse(json['marked_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class HistoryController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();

  final RxList<AttendanceHistoryRecord> records = <AttendanceHistoryRecord>[].obs;
  final RxBool isLoading = false.obs;
  final RxString errorMessage = ''.obs;

  // Statistics
  final RxInt totalCount     = 0.obs;
  final RxInt presentCount   = 0.obs;
  final RxInt reviewCount    = 0.obs;
  final RxInt rejectedCount  = 0.obs;

  @override
  void onInit() {
    super.onInit();
    loadHistory();
  }

  Future<void> loadHistory() async {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      final response = await _apiService.dio.get(ApiConstants.attendanceHistory);
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data as List<dynamic>;
        final parsed = data
            .map((e) => AttendanceHistoryRecord.fromJson(e as Map<String, dynamic>))
            .toList();
        records.assignAll(parsed);
        _computeStats();
      }
    } catch (e) {
      errorMessage.value = 'Failed to load attendance history.';
    } finally {
      isLoading.value = false;
    }
  }

  void _computeStats() {
    totalCount.value    = records.length;
    presentCount.value  = records.where((r) => r.attendanceStatus == 'present').length;
    reviewCount.value   = records.where((r) => r.attendanceStatus == 'manual_review').length;
    rejectedCount.value = records.where((r) => r.attendanceStatus == 'rejected').length;
  }

  double get attendanceRate {
    if (totalCount.value == 0) return 0.0;
    return (presentCount.value / totalCount.value) * 100.0;
  }
}
