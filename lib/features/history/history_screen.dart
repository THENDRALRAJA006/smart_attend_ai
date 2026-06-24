import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:intl/intl.dart';
import '../../core/services/auth_service.dart';
import '../../core/services/face_service.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/api_constants.dart';
import '../../app/routes/app_pages.dart';

class StudentDashboardController extends GetxController {
  final AuthService authService = Get.find<AuthService>();
  final FaceService _faceService = Get.find<FaceService>();
  final ApiService _apiService = Get.find<ApiService>();

  final RxBool isLoading = false.obs;
  final RxBool isFaceRegistered = false.obs;
  final RxInt embeddingsCount = 0.obs;
  final RxList attendanceHistory = [].obs;

  @override
  void onInit() {
    super.onInit();
    refreshDashboardData();
  }

  Future<void> refreshDashboardData() async {
    isLoading.value = true;
    await Future.wait([
      _fetchFaceStatus(),
      _fetchHistory(),
    ]);
    isLoading.value = false;
  }

  Future<void> _fetchFaceStatus() async {
    final status = await _faceService.getFaceRegistrationStatus();
    if (status != null) {
      isFaceRegistered.value = status['is_face_registered'] ?? false;
      embeddingsCount.value = status['embedding_count'] ?? 0;
    }
  }

  Future<void> _fetchHistory() async {
    try {
      final response = await _apiService.dio.get(ApiConstants.attendanceHistory);
      if (response.statusCode == 200) {
        attendanceHistory.value = response.data;
      }
    } catch (e) {
      // Interceptor alerts
    }
  }
}

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Inject controller inside screen
    final controller = Get.put(StudentDashboardController());

    return Scaffold(
      appBar: AppBar(
        title: const Text('Student Hub'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Color(0xFFFF4A75)),
            onPressed: () => controller.authService.logout(),
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => controller.refreshDashboardData(),
        color: const Color(0xFF6C63FF),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Profile Summary Card
              _buildProfileCard(controller),
              const SizedBox(height: 20),

              // 2. Face Registration Warning Banner
              Obx(() {
                if (controller.isFaceRegistered.value) {
                  return const SizedBox.shrink();
                }
                return _buildFaceWarningBanner();
              }),
              
              // 3. Mark Attendance Trigger
              Obx(() => controller.isFaceRegistered.value 
                ? _buildScanTriggerButton() 
                : const SizedBox.shrink()),
              const SizedBox(height: 24),

              // 4. History Logs Header
              Text(
                'Attendance Logs',
                style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
              ),
              const SizedBox(height: 12),

              // 5. History Logs List
              Obx(() {
                if (controller.isLoading.value && controller.attendanceHistory.isEmpty) {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(40.0),
                      child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
                    ),
                  );
                }

                if (controller.attendanceHistory.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(40.0),
                      child: Column(
                        children: [
                          Icon(Icons.history, size: 50, color: const Color(0xFF94A3B8).withOpacity(0.5)),
                          const SizedBox(height: 10),
                          const Text(
                            'No attendance records found.',
                            style: TextStyle(color: Color(0xFF94A3B8)),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: controller.attendanceHistory.length,
                  itemBuilder: (context, index) {
                    final record = controller.attendanceHistory[index];
                    return _buildHistoryItem(record);
                  },
                );
              }),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileCard(StudentDashboardController controller) {
    final user = controller.authService.currentUser;
    return Card(
      color: const Color(0xFF161722),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Row(
          children: [
            const CircleAvatar(
              radius: 30,
              backgroundColor: Color(0xFF6C63FF),
              child: Icon(Icons.school, size: 30, color: Colors.white),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user['name'] ?? 'Student User',
                    style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
                  ),
                  Text(
                    user['email'] ?? '',
                    style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                  ),
                  const SizedBox(height: 6),
                  Obx(() => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: controller.isFaceRegistered.value 
                          ? const Color(0xFF00FF87).withOpacity(0.1)
                          : const Color(0xFFFF4A75).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: controller.isFaceRegistered.value ? const Color(0xFF00FF87) : const Color(0xFFFF4A75),
                        width: 0.8
                      ),
                    ),
                    child: Text(
                      controller.isFaceRegistered.value 
                          ? 'FACE LOCKED (${controller.embeddingsCount.value}/50)' 
                          : 'FACE UNREGISTERED',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: controller.isFaceRegistered.value ? const Color(0xFF00FF87) : const Color(0xFFFF4A75),
                      ),
                    ),
                  )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFaceWarningBanner() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFF4A75).withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFF4A75), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.error_outline, color: Color(0xFFFF4A75)),
              SizedBox(width: 8),
              Text(
                'Registration Required',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'You must complete the 50-pose facial registration flow before you can mark your attendance.',
            style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF4A75),
              minimumSize: const Size(double.infinity, 44),
            ),
            onPressed: () => Get.toNamed(Routes.FACE_REGISTRATION),
            icon: const Icon(Icons.face),
            label: const Text('REGISTER FACE NOW'),
          )
        ],
      ),
    );
  }

  Widget _buildScanTriggerButton() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161722),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF232533), width: 1),
      ),
      child: Column(
        children: [
          const Text(
            'Active Class Attendance Session?',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 6),
          const Text(
            'Ensure Bluetooth is turned on, then tap below.',
            style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
          ),
          const SizedBox(height: 14),
          ElevatedButton.icon(
            onPressed: () => Get.toNamed(Routes.BLE_SCAN),
            icon: const Icon(Icons.bluetooth_searching),
            label: const Text('MARK ATTENDANCE'),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(dynamic record) {
    final status = record['attendance_status'];
    final similarity = record['similarity_score'] as double;
    final dateStr = record['date']; // YYYY-MM-DD
    final timeStr = record['time']; // HH:MM:SS
    
    Color statusColor = const Color(0xFFFF4A75);
    String statusLabel = 'Rejected';

    if (status == 'present') {
      statusColor = const Color(0xFF00FF87);
      statusLabel = 'Present';
    } else if (status == 'manual_review') {
      statusColor = const Color(0xFFFFD600);
      statusLabel = 'Review';
    }

    // Format Date nicely
    String formattedDate = dateStr;
    try {
      final parsedDate = DateTime.parse(dateStr);
      formattedDate = DateFormat('EEE, MMM d, yyyy').format(parsedDate);
    } catch (_) {}

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            // Status Icon color coded
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                status == 'present' 
                    ? Icons.check 
                    : status == 'manual_review' 
                        ? Icons.hourglass_empty 
                        : Icons.close,
                color: statusColor,
              ),
            ),
            const SizedBox(width: 14),
            // Text Details
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    record['subject_name'] ?? 'Class Subject',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15.0),
                  ),
                  Text(
                    '${record['subject_code'] ?? ''} • ${record['classroom_name'] ?? ''}',
                    style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12.0),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '$formattedDate at ${timeStr.substring(0, 5)}',
                    style: TextStyle(color: const Color(0xFF94A3B8).withOpacity(0.8), fontSize: 11.0),
                  ),
                ],
              ),
            ),
            // Badge / Score info
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    statusLabel.toUpperCase(),
                    style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Match: ${(similarity * 100).toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 11, color: const Color(0xFF94A3B8).withOpacity(0.8)),
                )
              ],
            ),
          ],
        ),
      ),
    );
  }
}
