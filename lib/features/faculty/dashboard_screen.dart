import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'faculty_controller.dart';
import '../../app/routes/app_pages.dart';

class FacultyDashboardScreen extends GetView<FacultyController> {
  const FacultyDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Faculty Command Center'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Color(0xFFFF4A75)),
            onPressed: () => controller.authService.logout(),
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => controller.checkActiveSession(),
        color: const Color(0xFF6C63FF),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // User Profile Banner
              _buildHeader(),
              const SizedBox(height: 24),

              // Active Session Status Card
              Obx(() => _buildActiveSessionCard()),
              const SizedBox(height: 24),

              // Faculty Actions Grid
              Text('Controls', style: Get.textTheme.titleLarge?.copyWith(color: Colors.white)),
              const SizedBox(height: 12),
              _buildControlsGrid(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    final user = controller.authService.currentUser;
    return Row(
      children: [
        const CircleAvatar(
          radius: 28,
          backgroundColor: Color(0xFF6C63FF),
          child: Icon(Icons.co_present, size: 28, color: Colors.white),
        ),
        const SizedBox(width: 16),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              user['name'] ?? 'Faculty Member',
              style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
            ),
            const Text(
              'Academic Faculty Panel',
              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
            ),
          ],
        )
      ],
    );
  }

  Widget _buildActiveSessionCard() {
    final hasSession = controller.hasActiveSession.value;
    final session = controller.activeSession;

    if (!hasSession) {
      return Card(
        color: const Color(0xFF161722),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              Icon(Icons.meeting_room_outlined, size: 48, color: const Color(0xFF94A3B8).withOpacity(0.5)),
              const SizedBox(height: 12),
              const Text(
                'No Active Session',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 6),
              const Text(
                'Launch a classroom session to begin capturing student BLE and QR attendance.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF94A3B8)),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: () => Get.toNamed(Routes.FACULTY_CREATE_SESSION),
                icon: const Icon(Icons.add),
                label: const Text('LAUNCH NEW SESSION'),
              )
            ],
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF6C63FF), Color(0xFF4A3AFF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'ACTIVE CLASS',
                  style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
              Obx(() => Text(
                '${controller.presentCount.value} Present',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              )),
            ],
          ),
          const SizedBox(height: 16),
          // We can show IDs or load name mappings. For demonstration, show basic info.
          Text(
            'Session ID: #${session['id']}',
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
          const SizedBox(height: 2),
          Text(
            'Running in Classroom #${session['classroom_id']}',
            style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Start Time: ${session['start_time'].toString().substring(11, 16)} UTC',
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildControlsGrid() {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      childAspectRatio: 1.3,
      children: [
        Obx(() => _buildControlTile(
          label: 'Live Monitor',
          icon: Icons.monitor,
          color: const Color(0xFF00D2FF),
          onTap: controller.hasActiveSession.value 
              ? () => Get.toNamed(Routes.FACULTY_LIVE_ATTENDANCE) 
              : null,
        )),
        Obx(() => _buildControlTile(
          label: 'Generate QR',
          icon: Icons.qr_code,
          color: const Color(0xFF6C63FF),
          onTap: controller.hasActiveSession.value 
              ? () => Get.toNamed(Routes.FACULTY_QR_GENERATE) 
              : null,
        )),
        Obx(() => _buildControlTile(
          label: 'Export CSV',
          icon: Icons.download,
          color: const Color(0xFF00FF87),
          onTap: controller.hasActiveSession.value 
              ? () => controller.downloadCSVReport() 
              : null,
        )),
        Obx(() => _buildControlTile(
          label: 'Close Session',
          icon: Icons.cancel,
          color: const Color(0xFFFF4A75),
          onTap: controller.hasActiveSession.value 
              ? () {
                  Get.defaultDialog(
                    title: 'Close Class Window',
                    middleText: 'Are you sure you want to end this attendance session?',
                    textConfirm: 'Yes, End',
                    textCancel: 'Cancel',
                    confirmTextColor: Colors.white,
                    buttonColor: const Color(0xFFFF4A75),
                    onConfirm: () {
                      Get.back();
                      controller.endSession();
                    }
                  );
                }
              : null,
        )),
      ],
    );
  }

  Widget _buildControlTile({
    required String label,
    required IconData icon,
    required Color color,
    VoidCallback? onTap,
  }) {
    final isEnabled = onTap != null;
    return Material(
      color: isEnabled ? const Color(0xFF161722) : const Color(0xFF10111A).withOpacity(0.5),
      borderRadius: BorderRadius.circular(16),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: isEnabled ? const Color(0xFF232533) : const Color(0xFF161722), 
          width: 1,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                icon,
                size: 32,
                color: isEnabled ? color : const Color(0xFF94A3B8).withOpacity(0.3),
              ),
              const SizedBox(height: 12),
              Text(
                label,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15.0,
                  color: isEnabled ? Colors.white : const Color(0xFF94A3B8).withOpacity(0.3),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
