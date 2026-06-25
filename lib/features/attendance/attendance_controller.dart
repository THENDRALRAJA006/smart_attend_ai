import 'dart:async';
import 'package:camera/camera.dart';
import 'package:dio/dio.dart' as dio_pkg;
import 'package:get/get.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../core/services/ble_service.dart';
import '../../core/services/liveness_service.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/api_constants.dart';
import '../../app/routes/app_pages.dart';

class AttendanceController extends GetxController {
  final BleService _bleService = Get.find<BleService>();
  final LivenessService _livenessService = Get.find<LivenessService>();
  final ApiService _apiService = Get.find<ApiService>();

  // State Observables
  final RxInt currentStep = 1.obs; // 1: BLE/QR, 2: Liveness, 3: Selfie, 4: Result
  final RxBool isLoading = false.obs;
  
  // Selection/Input Data
  int? selectedClassroomId;
  String selectedClassroomName = '';
  String? qrToken;

  // Liveness States
  String? challengeToken;
  final RxString currentChallenge = ''.obs; // 'blink' | 'smile' | 'turn_left' | 'turn_right'
  final RxInt livenessCountdown = 4.obs;
  final List<XFile> livenessFrames = [];
  Timer? _livenessTimer;
  Timer? _frameTimer;

  // Camera settings
  CameraController? cameraController;
  final RxBool isCameraInitialized = false.obs;

  // Result States
  final RxString resultStatus = ''.obs; // 'present' | 'manual_review' | 'rejected'
  final RxDouble similarityScore = 0.0.obs;
  final RxString resultMessage = ''.obs;

  @override
  void onInit() {
    super.onInit();
    // Start scanning on page load
    _bleService.startBeaconScan();
  }

  void selectClassroom(DetectedBeacon beacon) async {
    isLoading.value = true;
    _bleService.stopBeaconScan();

    // Fetch classroom ID from DB using classroom room name
    try {
      final response = await _apiService.dio.get(ApiConstants.adminClassrooms);
      if (response.statusCode == 200) {
        final List classrooms = response.data;
        final room = classrooms.firstWhere(
          (c) => c['room_name'].toString().toLowerCase() == beacon.roomName.toLowerCase(),
          orElse: () => null,
        );

        if (room != null) {
          selectedClassroomId = room['id'];
          selectedClassroomName = room['room_name'];
          qrToken = null; // Ensure QR token is empty for BLE path
          
          // Move to Step 2 (Liveness)
          currentStep.value = 2;
          await _setupLivenessChallenge();
        } else {
          Get.snackbar('Beacon Error', 'No matching classroom found in database.');
        }
      }
    } catch (e) {
      Get.snackbar('Network Error', 'Failed to retrieve classroom information.');
    }
    isLoading.value = false;
  }

  void processScannedQR(String qrCodeRaw) async {
    // Expected format: JSON or token string
    // Let's assume QR code stores the token string directly
    if (qrCodeRaw.isEmpty) return;

    _bleService.stopBeaconScan();
    qrToken = qrCodeRaw;
    selectedClassroomId = null;
    selectedClassroomName = 'QR Fallback Room';

    currentStep.value = 2;
    await _setupLivenessChallenge();
  }

  Future<void> _setupLivenessChallenge() async {
    isLoading.value = true;
    final challengeRes = await _livenessService.fetchChallenge();
    isLoading.value = false;

    if (challengeRes != null) {
      challengeToken = challengeRes.token;
      currentChallenge.value = challengeRes.challenge;
      
      // Initialize Front Camera for Liveness capture
      final bool initialized = await _initCamera();
      if (!initialized) {
        // Return to first step (BLE Scan) if camera couldn't be initialized
        currentStep.value = 1;
        _bleService.startBeaconScan();
        return;
      }
      
      // Start Countdown and record frames
      _startLivenessRecording();
    } else {
      Get.snackbar('Challenge Error', 'Failed to get liveness challenge. Retrying...');
      Get.back();
    }
  }

  Future<bool> _initCamera() async {
    try {
      final status = await Permission.camera.request();
      if (!status.isGranted) {
        Get.snackbar('Camera Permission', 'Camera permission is required for face liveness verification.');
        return false;
      }

      final cameras = await availableCameras();
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
      return true;
    } catch (e) {
      Get.snackbar('Camera Error', 'Could not open front camera.');
      return false;
    }
  }

  void _startLivenessRecording() {
    livenessCountdown.value = 4;
    livenessFrames.clear();

    _livenessTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (livenessCountdown.value > 1) {
        livenessCountdown.value--;
      } else {
        timer.cancel();
        _frameTimer?.cancel();
        await _verifyLiveness();
      }
    });

    // Capture 10 frames during the 3-4 seconds window
    int framesCount = 0;
    _frameTimer = Timer.periodic(const Duration(milliseconds: 300), (timer) async {
      if (framesCount < 10 && cameraController != null && cameraController!.value.isInitialized) {
        try {
          final XFile file = await cameraController!.takePicture();
          livenessFrames.add(file);
          framesCount++;
        } catch (e) {
          // ignore busy errors
        }
      } else {
        timer.cancel();
      }
    });
  }

  Future<void> _verifyLiveness() async {
    isLoading.value = true;
    if (challengeToken == null || livenessFrames.length < 5) {
      Get.snackbar('Capture Error', 'Incomplete facial frames captured. Retrying challenge...');
      isLoading.value = false;
      _startLivenessRecording();
      return;
    }

    final verifyRes = await _livenessService.verifyChallenge(
      challengeToken: challengeToken!,
      frameFiles: livenessFrames,
    );

    isLoading.value = false;

    if (verifyRes != null && verifyRes.verified) {
      // Store secondary token
      challengeToken = verifyRes.livenessToken;
      
      // Liveness passes, move to Step 3: Selfie Capture
      currentStep.value = 3;
    } else {
      Get.defaultDialog(
        title: 'Liveness Failed',
        middleText: verifyRes?.message ?? 'Spoofing challenge failed. Please follow instructions.',
        textConfirm: 'Retry',
        onConfirm: () {
          Get.back();
          _setupLivenessChallenge();
        },
        textCancel: 'Cancel',
        onCancel: () {
          Get.back();
          Get.offAllNamed(Routes.STUDENT_DASHBOARD);
        }
      );
    }
  }

  Future<void> submitSelfie() async {
    if (cameraController == null || !cameraController!.value.isInitialized) return;

    isLoading.value = true;
    try {
      // Capture selfie frame
      final XFile selfieFile = await cameraController!.takePicture();

      // Package request
      final dio_pkg.MultipartFile multipartSelfie = await dio_pkg.MultipartFile.fromFile(
        selfieFile.path,
        filename: 'selfie.jpg',
      );

      final Map<String, dynamic> formMap = {
        'selfie': multipartSelfie,
        'liveness_token': challengeToken,
      };

      if (qrToken != null) {
        formMap['qr_token'] = qrToken;
      } else {
        formMap['classroom_id'] = selectedClassroomId;
      }

      final formData = dio_pkg.FormData.fromMap(formMap);

      final response = await _apiService.dio.post(
        ApiConstants.attendanceVerify,
        data: formData,
        options: dio_pkg.Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        resultStatus.value = data['status'];
        similarityScore.value = data['similarity_score'] ?? 0.0;
        resultMessage.value = data['message'] ?? '';
        
        currentStep.value = 4; // Move to Result Screen
      }
    } catch (e) {
      // Dio interceptor alerts
    }
    isLoading.value = false;
  }

  void resetFlow() {
    _bleService.startBeaconScan();
    currentStep.value = 1;
    selectedClassroomId = null;
    selectedClassroomName = '';
    qrToken = null;
    challengeToken = null;
    livenessFrames.clear();
    cameraController?.dispose();
    cameraController = null;
    isCameraInitialized.value = false;
  }

  @override
  void onClose() {
    _livenessTimer?.cancel();
    _frameTimer?.cancel();
    cameraController?.dispose();
    super.onClose();
  }
}
