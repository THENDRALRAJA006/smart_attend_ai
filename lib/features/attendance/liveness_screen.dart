import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'attendance_controller.dart';

class LivenessScreen extends GetView<AttendanceController> {
  const LivenessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0E15),
      body: SafeArea(
        child: Obx(() {
          if (controller.currentStep.value == 3) {
            return const Center(child: Text('Navigating to Selfie...'));
          }

          if (!controller.isCameraInitialized.value) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
            );
          }

          final challenge = controller.currentChallenge.value.toUpperCase();
          
          return Stack(
            children: [
              // Main Scanner Body
              Column(
                children: [
                  const SizedBox(height: 20),
                  Text(
                    'Step 2: Anti-Spoofing Check',
                    style: Get.textTheme.titleLarge?.copyWith(color: Colors.white),
                  ),
                  const Text(
                    'Follow the animated action guide below.',
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
                            color: const Color(0xFF00D2FF),
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

                  // Animated Guide Footer Panel
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
                        _buildChallengeGraphic(challenge),
                        const SizedBox(height: 16),
                        Text(
                          _getChallengeInstruction(challenge),
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
                            'Time left: ${controller.livenessCountdown.value}s',
                            style: const TextStyle(
                              color: Color(0xFFFF4A75),
                              fontWeight: FontWeight.bold,
                              fontSize: 16.0,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Capturing frames: ${controller.livenessFrames.length} / 10',
                          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12.0),
                        )
                      ],
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
                        CircularProgressIndicator(color: Color(0xFF00D2FF)),
                        SizedBox(height: 20),
                        Text(
                          'Verifying liveness challenge...',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Scanning frames for verification.',
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

  Widget _buildChallengeGraphic(String challenge) {
    if (challenge == 'BLINK') {
      return const Icon(
        Icons.remove_red_eye,
        size: 50,
        color: Color(0xFF00D2FF),
      );
    } else if (challenge == 'SMILE') {
      return const Icon(
        Icons.sentiment_very_satisfied,
        size: 50,
        color: Color(0xFF00D2FF),
      );
    } else if (challenge == 'TURN_LEFT') {
      return const Icon(
        Icons.arrow_back_rounded,
        size: 50,
        color: Color(0xFF00D2FF),
      );
    } else if (challenge == 'TURN_RIGHT') {
      return const Icon(
        Icons.arrow_forward_rounded,
        size: 50,
        color: Color(0xFF00D2FF),
      );
    }
    return const Icon(Icons.face, size: 50, color: Color(0xFF00D2FF));
  }

  String _getChallengeInstruction(String challenge) {
    if (challenge == 'BLINK') {
      return 'Blink slowly';
    } else if (challenge == 'SMILE') {
      return 'Smile naturally';
    } else if (challenge == 'TURN_LEFT') {
      return 'Turn your head left';
    } else if (challenge == 'TURN_RIGHT') {
      return 'Turn your head right';
    }
    return 'Look straight ahead';
  }
}
