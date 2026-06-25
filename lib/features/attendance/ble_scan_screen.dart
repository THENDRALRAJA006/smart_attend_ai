import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:permission_handler/permission_handler.dart';
import 'attendance_controller.dart';
import '../../core/services/ble_service.dart';

class BleScanScreen extends StatefulWidget {
  const BleScanScreen({super.key});

  @override
  State<BleScanScreen> createState() => _BleScanScreenState();
}

class _BleScanScreenState extends State<BleScanScreen> with SingleTickerProviderStateMixin {
  final AttendanceController controller = Get.find<AttendanceController>();
  final BleService bleService = Get.find<BleService>();
  bool showQRScanner = false;
  late AnimationController _radarAnimController;

  @override
  void initState() {
    super.initState();
    _radarAnimController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _radarAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mark Attendance'),
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            bleService.stopBeaconScan();
            Get.back();
          },
        ),
      ),
      body: Obx(() {
        if (controller.currentStep.value == 2) {
          return const Center(child: Text('Navigating to Liveness...'));
        }

        return SafeArea(
          child: showQRScanner ? _buildQRScanner() : _buildBLEScanner(),
        );
      }),
    );
  }

  Widget _buildBLEScanner() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          // Radar Animation Header
          Center(
            child: Stack(
              alignment: Alignment.center,
              children: [
                AnimatedBuilder(
                  animation: _radarAnimController,
                  builder: (context, child) {
                    return Container(
                      width: 180,
                      height: 180,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: const Color(0xFF6C63FF).withOpacity(1 - _radarAnimController.value),
                          width: 2.0 + (8.0 * _radarAnimController.value),
                        ),
                      ),
                    );
                  },
                ),
                Container(
                  width: 140,
                  height: 140,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF161722),
                    border: Border.all(color: const Color(0xFF232533), width: 1.5),
                  ),
                  child: const Icon(
                    Icons.bluetooth_searching,
                    size: 50,
                    color: Color(0xFF00D2FF),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Scanning for beacons...',
            style: Get.textTheme.titleLarge,
          ),
          const Text(
            'Move closer to the faculty desk beacon to begin.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Color(0xFF94A3B8)),
          ),
          const SizedBox(height: 30),

          // Found classrooms list
          Expanded(
            child: Obx(() {
              if (bleService.detectedBeacons.isEmpty) {
                return const Center(
                  child: Text(
                    'No classrooms found nearby.',
                    style: TextStyle(color: Color(0xFF94A3B8)),
                  ),
                );
              }

              return ListView.builder(
                itemCount: bleService.detectedBeacons.length,
                itemBuilder: (context, index) {
                  final beacon = bleService.detectedBeacons[index];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      leading: const CircleAvatar(
                        backgroundColor: Color(0xFF6C63FF),
                        child: Icon(Icons.meeting_room_outlined, color: Colors.white),
                      ),
                      title: Text(beacon.roomName, style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Signal: ${beacon.rssi} dBm (UUID: ...${beacon.uuid.substring(beacon.uuid.length - 8)})'),
                      trailing: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(80, 36),
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                        ),
                        onPressed: () => controller.selectClassroom(beacon),
                        child: const Text('JOIN'),
                      ),
                    ),
                  );
                },
              );
            }),
          ),
          const SizedBox(height: 16),

          // QR Code fallback option
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(double.infinity, 50),
              side: const BorderSide(color: Color(0xFF00D2FF)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () async {
              final status = await Permission.camera.request();
              if (status.isGranted) {
                setState(() {
                  showQRScanner = true;
                });
              } else {
                Get.snackbar(
                  'Camera Permission',
                  'Camera permission is required to use the QR scanner.',
                  snackPosition: SnackPosition.BOTTOM,
                  backgroundColor: const Color(0xFF161722),
                  colorText: Colors.white,
                );
              }
            },
            icon: const Icon(Icons.qr_code_scanner, color: Color(0xFF00D2FF)),
            label: const Text('QR FALLBACK SCANNER', style: TextStyle(color: Color(0xFF00D2FF), fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildQRScanner() {
    return Stack(
      children: [
        MobileScanner(
          onDetect: (capture) {
            final List<Barcode> barcodes = capture.barcodes;
            if (barcodes.isNotEmpty) {
              final String code = barcodes.first.rawValue ?? '';
              controller.processScannedQR(code);
              setState(() {
                showQRScanner = false;
              });
            }
          },
        ),
        // Close scanner
        Positioned(
          top: 20,
          left: 20,
          child: FloatingActionButton(
            backgroundColor: const Color(0xFF161722),
            onPressed: () {
              setState(() {
                showQRScanner = false;
              });
              bleService.startBeaconScan();
            },
            child: const Icon(Icons.close, color: Colors.white),
          ),
        ),
        // Guide Overlay Box
        Center(
          child: Container(
            width: 250,
            height: 250,
            decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFF00D2FF), width: 3),
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        ),
      ],
    );
  }
}
