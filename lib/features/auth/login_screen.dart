import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'auth_controller.dart';

class LoginScreen extends GetView<AuthController> {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Header Logo / Branding
                const Icon(
                  Icons.fingerprint,
                  size: 80,
                  color: Color(0xFF6C63FF),
                ),
                const SizedBox(height: 16),
                Text(
                  'SMARTATTEND AI',
                  style: Get.textTheme.headlineLarge?.copyWith(
                    color: Colors.white,
                    letterSpacing: 1.5,
                  ),
                ),
                Text(
                  'Secure Proximity Face Attendance',
                  style: Get.textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFF94A3B8),
                  ),
                ),
                const SizedBox(height: 40),

                // Card Container
                Obx(() => Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Title
                        Text(
                          controller.isRegisterMode.value ? 'Student Registration' : 'Account Login',
                          style: Get.textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 20),

                        // Role Selector Tabs (Only show when not in Registration mode)
                        if (!controller.isRegisterMode.value) ...[
                          _buildRoleSelector(),
                          const SizedBox(height: 20),
                        ],

                        // Registration fields
                        if (controller.isRegisterMode.value) ...[
                          TextField(
                            controller: controller.nameController,
                            decoration: const InputDecoration(
                              labelText: 'Full Name',
                              prefixIcon: Icon(Icons.person_outline),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: controller.rollNoController,
                            decoration: const InputDecoration(
                              labelText: 'Roll Number',
                              prefixIcon: Icon(Icons.badge_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: controller.departmentController,
                                  decoration: const InputDecoration(
                                    labelText: 'Department',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: controller.yearController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(
                                    labelText: 'Year',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: controller.sectionController,
                                  decoration: const InputDecoration(
                                    labelText: 'Section',
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                        ],

                        // Standard Credentials
                        TextField(
                          controller: controller.emailController,
                          keyboardType: TextInputType.emailAddress,
                          decoration: const InputDecoration(
                            labelText: 'Email Address',
                            prefixIcon: Icon(Icons.email_outlined),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: controller.passwordController,
                          obscureText: true,
                          decoration: const InputDecoration(
                            labelText: 'Password',
                            prefixIcon: Icon(Icons.lock_outlined),
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Submit Button
                        controller.isLoading.value
                            ? const Center(
                                child: CircularProgressIndicator(
                                  color: Color(0xFF6C63FF),
                                ),
                              )
                            : ElevatedButton(
                                onPressed: () => controller.submit(),
                                child: Text(
                                  controller.isRegisterMode.value ? 'REGISTER' : 'LOG IN',
                                ),
                              ),
                        const SizedBox(height: 16),

                        // Register mode toggle
                        if (controller.selectedRole.value == 'student')
                          Center(
                            child: TextButton(
                              onPressed: () => controller.toggleMode(),
                              child: Text(
                                controller.isRegisterMode.value
                                    ? 'Already have an account? Login'
                                    : 'Create Student Account',
                                style: const TextStyle(
                                  color: Color(0xFF00D2FF),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                )),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRoleSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF0D0E15),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          _buildRoleTab('Student', 'student'),
          _buildRoleTab('Faculty', 'faculty'),
          _buildRoleTab('Admin', 'admin'),
        ],
      ),
    );
  }

  Widget _buildRoleTab(String label, String role) {
    return Expanded(
      child: Obx(() {
        final isSelected = controller.selectedRole.value == role;
        return GestureDetector(
          onTap: () {
            controller.selectedRole.value = role;
          },
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: isSelected ? const Color(0xFF6C63FF) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13.0,
                color: isSelected ? Colors.white : const Color(0xFF94A3B8),
              ),
            ),
          ),
        );
      }),
    );
  }
}
