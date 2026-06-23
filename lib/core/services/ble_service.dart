import 'dart:async';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:get/get.dart';
import 'package:permission_handler/permission_handler.dart';

class DetectedBeacon {
  final String roomName;
  final String uuid;
  final int rssi;

  DetectedBeacon({required this.roomName, required this.uuid, required this.rssi});
}

class BleService extends GetxService {
  final RxList<DetectedBeacon> detectedBeacons = <DetectedBeacon>[].obs;
  final RxBool isScanning = false.obs;
  StreamSubscription? _scanSubscription;

  Future<bool> requestPermissions() async {
    Map<Permission, PermissionStatus> statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();

    return statuses.values.every((status) => status.isGranted);
  }

  Future<void> startBeaconScan() async {
    final permissionsGranted = await requestPermissions();
    if (!permissionsGranted) {
      Get.snackbar('Permissions Required', 'Bluetooth and Location permissions are required to scan for classrooms.');
      return;
    }

    if (isScanning.value) return;

    detectedBeacons.clear();
    isScanning.value = true;

    try {
      // Listen to scan results
      _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
        for (ScanResult r in results) {
          final deviceName = r.advertisementData.localName;
          
          if (deviceName.startsWith('SMARTATTEND_')) {
            final roomName = deviceName.replaceFirst('SMARTATTEND_', '');
            final uuid = r.device.remoteId.str;
            final rssi = r.rssi;

            // Check if already in list, if so, update RSSI
            final index = detectedBeacons.indexWhere((b) => b.roomName == roomName);
            if (index != -1) {
              detectedBeacons[index] = DetectedBeacon(
                roomName: roomName,
                uuid: uuid,
                rssi: rssi,
              );
            } else {
              detectedBeacons.add(DetectedBeacon(
                roomName: roomName,
                uuid: uuid,
                rssi: rssi,
              ));
            }
          }
        }
      });

      // Start scanning (timeout after 10 seconds)
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 10));
      
      // Monitor when scanning stops
      FlutterBluePlus.isScanning.listen((scanning) {
        isScanning.value = scanning;
        if (!scanning) {
          _scanSubscription?.cancel();
        }
      });
    } catch (e) {
      isScanning.value = false;
      Get.snackbar('Scan Error', 'Failed to start BLE scan: $e');
    }
  }

  void stopBeaconScan() {
    FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();
    isScanning.value = false;
  }

  @override
  void onClose() {
    stopBeaconScan();
    super.onClose();
  }
}
