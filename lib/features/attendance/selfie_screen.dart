import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'attendance_controller.dart';
import '../../app/routes/app_pages.dart';

class SelfieScreen extends GetView<AttendanceController> {
  const SelfieScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0E15),
      appBar: AppBar(
        title: Obx(() => Text(
          controller.currentStep.value == 4 ? 'Attendance Result' : 'Face Verification',
        )),
        centerTitle: true,
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Obx(() {
          if (controller.currentStep.value == 4) {
            return _buildResultScreen();
          }

          if (!controller.isCameraInitialized.value) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
            );
          }

          return Stack(
            children: [
              // Scanner flow layout
              Column(
                children: [
                  const SizedBox(height: 20),
                  Text(
                    'Step 3: Capture Selfie',
                    style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
                  ),
                  const Text(
                    'Fit your face inside the oval frame.',
                    style: TextStyle(color: Color(0xFF94A3B8)),
                  ),
                  const SizedBox(height: 30),

                  // Camera Preview in Oval Shape
                  Expanded(
                    child: Center(
                      child: Container(
                        width: 280,
                        height: 380,
                        decoration: BoxDecoration(
                          shape: BoxShape.rectangle,
                          borderRadius: BorderRadius.circular(140),
                          border: Border.all(
                            color: const Color(0xFF6C63FF),
                            width: 3.0,
                          ),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(140),
                          child: AspectRatio(
                            aspectRatio: controller.cameraController!.value.aspectRatio,
                            child: CameraPreview(controller.cameraController!),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),

                  // Capture Control Button
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
                    child: ElevatedButton.icon(
                      onPressed: () => controller.submitSelfie(),
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('CONFIRM & VERIFY'),
                    ),
                  ),
                ],
              ),

              // Processing overlay
              if (controller.isLoading.value)
                Container(
                  color: Colors.black.withOpacity(0.8),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: Color(0xFF6C63FF)),
                        SizedBox(height: 20),
                        Text(
                          'Verifying identity...',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Comparing face with 50 stored embeddings.',
                          style: TextStyle(color: Color(0xFF94A3B8)),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        }),
      ),
    );
  }

  Widget _buildResultScreen() {
    final status = controller.resultStatus.value;
    final score = controller.similarityScore.value;
    final msg = controller.resultMessage.value;

    Color statusColor = const Color(0xFFFF4A75); // default red (rejected)
    IconData statusIcon = Icons.cancel;
    String statusTitle = 'Verification Failed';

    if (status == 'present') {
      statusColor = const Color(0xFF00FF87);
      statusIcon = Icons.check_circle;
      statusTitle = 'Attendance Marked';
    } else if (status == 'manual_review') {
      statusColor = const Color(0xFFFFD600);
      statusIcon = Icons.warning;
      statusTitle = 'Pending Faculty Review';
    }

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Spacer(),
          // Score / Icon card
          Container(
            width: 140,
            height: 140,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: statusColor.withOpacity(0.15),
              border: Border.all(color: statusColor, width: 3),
            ),
            child: Icon(
              statusIcon,
              size: 70,
              color: statusColor,
            ),
          ),
          const SizedBox(height: 30),

          // Title
          Text(
            statusTitle,
            style: Get.textTheme.headlineMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          
          // Message
          Text(
            msg,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 16.0),
          ),
          const SizedBox(height: 24),

          // Similarity Metric Card
          Card(
            color: const Color(0xFF161722),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
              child: Column(
                children: [
                  const Text('FACE MATCH SIMILARITY', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11.0, letterSpacing: 1.0)),
                  const SizedBox(height: 4),
                  Text(
                    '${(score * 100).toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 32.0,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const Spacer(),

          // Go back button
          ElevatedButton(
            onPressed: () {
              controller.resetFlow();
              Get.offAllNamed(Routes.STUDENT_DASHBOARD);
            },
            child: const Text('BACK TO DASHBOARD'),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
