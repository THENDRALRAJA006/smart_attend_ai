import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'faculty_controller.dart';

class QrGenerateScreen extends StatefulWidget {
  const QrGenerateScreen({super.key});

  @override
  State<QrGenerateScreen> createState() => _QrGenerateScreenState();
}

class _QrGenerateScreenState extends State<QrGenerateScreen> {
  final FacultyController controller = Get.find<FacultyController>();

  @override
  void initState() {
    super.initState();
    // Request initial QR token immediately on load
    controller.generateQRToken();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dynamic QR Fallback'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),
              Text(
                'Student Scan Target',
                style: Get.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const Text(
                'Students can scan this code using the fallback scanner to bypass BLE beacon verification.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF94A3B8)),
              ),
              const SizedBox(height: 40),

              // QR Code Card
              Obx(() {
                if (controller.qrToken.value.isEmpty) {
                  return const Center(child: CircularProgressIndicator(color: Color(0xFF6C63FF)));
                }

                return Card(
                  color: Colors.white, // QR codes need light backgrounds to remain readable by camera scanners
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: QrImageView(
                      data: controller.qrToken.value,
                      version: QrVersions.auto,
                      size: 260.0,
                      eyeStyle: const QrEyeStyle(
                        eyeShape: QrEyeShape.square,
                        color: Color(0xFF0D0E15),
                      ),
                      dataModuleStyle: const QrDataModuleStyle(
                        dataModuleShape: QrDataModuleShape.square,
                        color: Color(0xFF0D0E15),
                      ),
                    ),
                  ),
                );
              }),
              const SizedBox(height: 30),

              // Countdown timer badge
              Obx(() => Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: controller.qrTimeLeft.value > 10
                      ? const Color(0xFF161722)
                      : const Color(0xFFFF4A75).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: controller.qrTimeLeft.value > 10 ? const Color(0xFF232533) : const Color(0xFFFF4A75),
                    width: 1.2
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.timer_outlined,
                      color: controller.qrTimeLeft.value > 10 ? const Color(0xFF00D2FF) : const Color(0xFFFF4A75),
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Refreshing in: ${controller.qrTimeLeft.value}s',
                      style: TextStyle(
                        color: controller.qrTimeLeft.value > 10 ? Colors.white : const Color(0xFFFF4A75),
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ],
                ),
              )),

              const Spacer(),

              // Quick Actions
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size(0, 50),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        side: const BorderSide(color: Color(0xFF232533)),
                      ),
                      onPressed: () => controller.generateQRToken(),
                      icon: const Icon(Icons.refresh, color: Colors.white),
                      label: const Text('FORCE REFRESH', style: TextStyle(color: Colors.white)),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        minimumSize: const Size(0, 50),
                        backgroundColor: const Color(0xFF6C63FF),
                      ),
                      onPressed: () {
                        Get.snackbar(
                          'Share Triggered',
                          'QR code shared successfully.',
                          backgroundColor: const Color(0xFF6C63FF).withOpacity(0.2),
                          colorText: Colors.white,
                        );
                      },
                      icon: const Icon(Icons.share),
                      label: const Text('SHARE QR'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
