import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'faculty_controller.dart';

class LiveAttendanceScreen extends GetView<FacultyController> {
  const LiveAttendanceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Real-Time Attendance Roll'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Statistics Top Header Card
              _buildStatsCard(),
              const SizedBox(height: 20),

              Text(
                'Live Log List',
                style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
              ),
              const SizedBox(height: 10),

              // Streaming/Polling list
              Expanded(
                child: Obx(() {
                  if (controller.liveLogs.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(color: Color(0xFF00D2FF)),
                          SizedBox(height: 16),
                          Text(
                            'Waiting for student submissions...',
                            style: TextStyle(color: Color(0xFF94A3B8), fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.builder(
                    itemCount: controller.liveLogs.length,
                    itemBuilder: (context, index) {
                      final log = controller.liveLogs[index];
                      return _buildLiveLogItem(log);
                    },
                  );
                }),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatsCard() {
    return Card(
      color: const Color(0xFF161722),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Column(
              children: [
                const Text('PRESENT STUDENTS', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11, letterSpacing: 0.5)),
                const SizedBox(height: 4),
                Obx(() => Text(
                  '${controller.presentCount.value}',
                  style: const TextStyle(color: Color(0xFF00FF87), fontSize: 36, fontWeight: FontWeight.w900),
                )),
              ],
            ),
            Container(width: 1, height: 50, color: const Color(0xFF232533)),
            Column(
              children: [
                const Text('PENDING REVIEW', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11, letterSpacing: 0.5)),
                const SizedBox(height: 4),
                Obx(() {
                  final reviews = controller.liveLogs.where((l) => l['status'] == 'manual_review').length;
                  return Text(
                    '$reviews',
                    style: const TextStyle(color: Color(0xFFFFD600), fontSize: 36, fontWeight: FontWeight.w900),
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLiveLogItem(dynamic log) {
    final status = log['status'];
    final score = log['similarity_score'] as double;
    final timeStr = log['time'] as String;

    Color statusColor = const Color(0xFFFF4A75);
    Color cardBorder = const Color(0xFF232533);
    Color cardBg = const Color(0xFF161722);

    if (status == 'present') {
      statusColor = const Color(0xFF00FF87);
    } else if (status == 'manual_review') {
      statusColor = const Color(0xFFFFD600);
      cardBorder = const Color(0xFFFFD600).withOpacity(0.5);
      cardBg = const Color(0xFFFFD600).withOpacity(0.04);
    }

    return Card(
      color: cardBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: cardBorder, width: 1),
      ),
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: statusColor.withOpacity(0.1),
                  child: Icon(
                    status == 'present'
                        ? Icons.check_circle_outline
                        : status == 'manual_review'
                            ? Icons.warning_amber_outlined
                            : Icons.cancel_outlined,
                    color: statusColor,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        log['student_name'] ?? 'Student Name',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16.0),
                      ),
                      Text(
                        'Roll: ${log['roll_no']} • marked at $timeStr',
                        style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12.0),
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Match: ${(score * 100).toStringAsFixed(1)}%',
                      style: TextStyle(
                        color: statusColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 14.0,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      status.toString().replaceAll('_', ' ').toUpperCase(),
                      style: TextStyle(color: statusColor.withOpacity(0.7), fontSize: 9, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),

            // Manual Review Actions
            if (status == 'manual_review') ...[
              const Divider(color: Color(0xFF232533), height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      foregroundColor: const Color(0xFFFF4A75),
                    ),
                    onPressed: () => controller.reviewOverride(log['id'], false),
                    icon: const Icon(Icons.close, size: 16),
                    label: const Text('REJECT'),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00FF87),
                      foregroundColor: Colors.black,
                      minimumSize: const Size(110, 36),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: () => controller.reviewOverride(log['id'], true),
                    icon: const Icon(Icons.check, size: 16),
                    label: const Text('APPROVE'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
