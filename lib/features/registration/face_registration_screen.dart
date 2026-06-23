import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'face_registration_controller.dart';

class FaceRegistrationScreen extends GetView<FaceRegistrationController> {
  const FaceRegistrationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0E15),
      body: SafeArea(
        child: Obx(() {
          if (!controller.isCameraInitialized.value) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
            );
          }

          return Stack(
            children: [
              // Main Camera Stream & Scanner UI
              Column(
                children: [
                  const SizedBox(height: 20),
                  // Progress indicator
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Face Scan Registry',
                              style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
                            ),
                            Text(
                              '${controller.currentPoseIndex.value + 1} / ${controller.poses.length} Poses',
                              style: const TextStyle(color: Color(0xFF00D2FF), fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        LinearProgressIndicator(
                          value: (controller.currentPoseIndex.value) / controller.poses.length,
                          backgroundColor: const Color(0xFF1E202E),
                          valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6C63FF)),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 30),

                  // Oval Mask Camera Preview
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
                  const SizedBox(height: 30),

                  // Prompt instructions panel
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                    decoration: const BoxDecoration(
                      color: Color(0xFF161722),
                      borderRadius: BorderRadius.only(
                        topLeft: Radius.circular(24),
                        topRight: Radius.circular(24),
                      ),
                      border: Border(
                        top: BorderSide(color: Color(0xFF232533), width: 1),
                      ),
                    ),
                    child: Column(
                      children: [
                        Text(
                          'Pose Instruction',
                          style: Get.textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFF94A3B8),
                            letterSpacing: 1.0,
                          ),
                        ),
                        const SizedBox(height: 8),
                        if (controller.currentPoseIndex.value < controller.poses.length)
                          Text(
                            controller.poses[controller.currentPoseIndex.value],
                            textAlign: TextAlign.center,
                            style: Get.textTheme.headlineMedium?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0D0E15),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Hold pose for ${controller.timerCountdown.value}s',
                            style: const TextStyle(
                              color: Color(0xFF00D2FF),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Frames buffered: ${controller.framesCaptured.value} / 120',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: const Color(0xFF94A3B8).withOpacity(0.8),
                          ),
                        )
                      ],
                    ),
                  )
                ],
              ),

              // Processing/Uploading Blur Overlay
              if (controller.isProcessing.value)
                Container(
                  color: Colors.black.withOpacity(0.8),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: Color(0xFF6C63FF)),
                        SizedBox(height: 20),
                        Text(
                          'Extracting facial embeddings...',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Selecting 50 best frames. Please wait.',
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
}
