import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/services/auth_service.dart';
import '../../core/services/face_service.dart';
import '../../app/routes/app_pages.dart';

class AuthController extends GetxController {
  final AuthService _authService = Get.find<AuthService>();
  final FaceService _faceService = Get.find<FaceService>();

  final RxBool isLoading = false.obs;
  final RxString selectedRole = 'student'.obs; // 'student' | 'faculty' | 'admin'
  final RxBool isRegisterMode = false.obs; // Toggle registration (students only)

  // Form Fields
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  
  // Registration specific fields
  final nameController = TextEditingController();
  final rollNoController = TextEditingController();
  final departmentController = TextEditingController();
  final yearController = TextEditingController();
  final sectionController = TextEditingController();

  void toggleMode() {
    isRegisterMode.value = !isRegisterMode.value;
    clearInputs();
  }

  void clearInputs() {
    emailController.clear();
    passwordController.clear();
    nameController.clear();
    rollNoController.clear();
    departmentController.clear();
    yearController.clear();
    sectionController.clear();
  }

  Future<void> submit() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      Get.snackbar('Input Error', 'Please enter email and password.');
      return;
    }

    isLoading.value = true;

    if (isRegisterMode.value && selectedRole.value == 'student') {
      // Registration Flow
      final name = nameController.text.trim();
      final rollNo = rollNoController.text.trim();
      final dept = departmentController.text.trim();
      final yearStr = yearController.text.trim();
      final section = sectionController.text.trim();

      if (name.isEmpty || rollNo.isEmpty || dept.isEmpty || yearStr.isEmpty || section.isEmpty) {
        Get.snackbar('Input Error', 'All registration fields are required.');
        isLoading.value = false;
        return;
      }

      final year = int.tryParse(yearStr);
      if (year == null) {
        Get.snackbar('Input Error', 'Academic Year must be a valid number.');
        isLoading.value = false;
        return;
      }

      final success = await _authService.registerStudent(
        name: name,
        rollNo: rollNo,
        email: email,
        password: password,
        department: dept,
        year: year,
        section: section,
      );

      if (success) {
        // Since face registration is not yet completed for new students,
        // route directly to the face scanner
        Get.offAllNamed(Routes.FACE_REGISTRATION);
      }
    } else {
      // Login Flow
      final success = await _authService.login(
        email: email,
        password: password,
        role: selectedRole.value,
      );

      if (success) {
        _navigateByUserRole();
      }
    }
    isLoading.value = false;
  }

  Future<void> _navigateByUserRole() async {
    final role = _authService.userRole.value;
    if (role == 'student') {
      // Check if student has registered face embeddings
      final faceStatus = await _faceService.getFaceRegistrationStatus();
      if (faceStatus != null && faceStatus['is_face_registered'] == true) {
        Get.offAllNamed(Routes.STUDENT_DASHBOARD);
      } else {
        Get.offAllNamed(Routes.FACE_REGISTRATION);
      }
    } else if (role == 'faculty') {
      Get.offAllNamed(Routes.FACULTY_DASHBOARD);
    } else if (role == 'admin') {
      Get.offAllNamed(Routes.ADMIN_DASHBOARD);
    }
  }

  @override
  void onClose() {
    emailController.dispose();
    passwordController.dispose();
    nameController.dispose();
    rollNoController.dispose();
    departmentController.dispose();
    yearController.dispose();
    sectionController.dispose();
    super.onClose();
  }
}
