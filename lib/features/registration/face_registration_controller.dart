import 'dart:async';
import 'package:camera/camera.dart';
import 'package:get/get.dart';
import '../../core/services/face_service.dart';
import '../../app/routes/app_pages.dart';

class FaceRegistrationController extends GetxController {
  final FaceService _faceService = Get.find<FaceService>();

  CameraController? cameraController;
  final RxBool isCameraInitialized = false.obs;
  final RxBool isProcessing = false.obs;

  // Poses List
  final List<String> poses = [
    'Look straight ahead',
    'Smile naturally',
    'Blink slowly',
    'Turn head left 15°',
    'Turn head right 15°',
    'Turn head left 30°',
    'Turn head right 30°',
    'Look up slightly',
    'Look down slightly',
    'Neutral expression',
    'Slight smile',
    'With glasses (if applicable)',
    'Look towards a bright light',
    'Indoor ambient light',
    'Normal face'
  ];

  final RxInt currentPoseIndex = 0.obs;
  final RxInt timerCountdown = 3.obs;
  final RxInt framesCaptured = 0.obs;
  final List<XFile> capturedFrames = [];

  Timer? _poseTimer;
  Timer? _frameCaptureTimer;

  @override
  void onInit() {
    super.onInit();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        Get.snackbar('Camera Error', 'No cameras detected on this device.');
        return;
      }

      // Select front-facing camera
      final frontCamera = cameras.firstWhere(
        (cam) => cam.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      cameraController = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await cameraController!.initialize();
      isCameraInitialized.value = true;
      
      // Start the guided pose capture loop after a short delay
      Future.delayed(const Duration(seconds: 1), _startGuidedCapture);
    } catch (e) {
      Get.snackbar('Camera Error', 'Failed to initialize camera: $e');
    }
  }

  void _startGuidedCapture() {
    currentPoseIndex.value = 0;
    framesCaptured.value = 0;
    capturedFrames.clear();
    
    _nextPose();
  }

  void _nextPose() {
    if (currentPoseIndex.value >= poses.length) {
      // Completed all poses, upload frames
      _uploadRegistrationFrames();
      return;
    }

    timerCountdown.value = 3;

    // Start 3-second countdown timer for this pose
    _poseTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (timerCountdown.value > 1) {
        timerCountdown.value--;
      } else {
        timer.cancel();
        _frameCaptureTimer?.cancel();
        currentPoseIndex.value++;
        _nextPose();
      }
    });

    // Capture 8 frames evenly spaced during the 3-second interval (approx one every 350ms)
    int framesForThisPose = 0;
    _frameCaptureTimer = Timer.periodic(const Duration(milliseconds: 350), (timer) async {
      if (framesForThisPose < 8 && cameraController != null && cameraController!.value.isInitialized) {
        try {
          final XFile file = await cameraController!.takePicture();
          capturedFrames.add(file);
          framesCaptured.value = capturedFrames.length;
          framesForThisPose++;
        } catch (e) {
          // Skip frame if camera is busy
        }
      } else {
        timer.cancel();
      }
    });
  }

  Future<void> _uploadRegistrationFrames() async {
    isProcessing.value = true;
    _poseTimer?.cancel();
    _frameCaptureTimer?.cancel();

    Get.snackbar(
      'Capturing Complete',
      'Uploading and analyzing 120 facial poses. Please wait...',
      duration: const Duration(seconds: 5),
    );

    final result = await _faceService.registerStudentFace(capturedFrames);
    isProcessing.value = false;

    if (result != null) {
      Get.snackbar('Registration Successful', result['message'] ?? 'Facial registration completed.');
      Get.offAllNamed(Routes.STUDENT_DASHBOARD);
    } else {
      Get.defaultDialog(
        title: 'Registration Failed',
        middleText: 'Could not extract high-quality embeddings. Would you like to try again?',
        textConfirm: 'Yes, Retry',
        textCancel: 'Cancel',
        onConfirm: () {
          Get.back(); // close dialog
          _startGuidedCapture(); // restart
        },
        onCancel: () {
          Get.back();
          Get.offAllNamed(Routes.LOGIN);
        }
      );
    }
  }

  @override
  void onClose() {
    _poseTimer?.cancel();
    _frameCaptureTimer?.cancel();
    cameraController?.dispose();
    super.onClose();
  }
}
