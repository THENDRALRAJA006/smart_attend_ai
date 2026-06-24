/*
 * SmartAttend AI — ESP32 BLE Proximity Beacon
 * ═════════════════════════════════════════════
 * Broadcasts a BLE advertising packet that Flutter's flutter_blue_plus
 * can detect for proximity-based attendance verification.
 *
 * Configuration: edit the #define constants below.
 * Upload via Arduino IDE with "ESP32 Dev Module" board selected.
 *
 * Required library: ESP32 BLE Arduino (bundled with esp32 board package)
 *
 * Hardware: ESP32 DevKit v1 (or any ESP32 module)
 * LED_PIN: GPIO2 (built-in LED on most DevKit boards)
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLEAdvertising.h>
#include <BLEBeacon.h>
#include <esp_sleep.h>

// ─────────────────────────────────────────────────────────────────────────────
// CONFIGURATION — Edit these values for each room deployment
// ─────────────────────────────────────────────────────────────────────────────

// Device name prefix MUST start with "SMARTATTEND_"
// Flutter filters by this prefix to identify SmartAttend beacons
#define ROOM_NAME         "ROOM101"
#define DEVICE_NAME       "SMARTATTEND_" ROOM_NAME

// Unique UUID per beacon/room (generate at https://www.uuidgenerator.net/)
#define BEACON_UUID       "12345678-1234-1234-1234-123456789ABC"

// Major / Minor values (optional — can encode building/floor info)
#define BEACON_MAJOR      0x0001
#define BEACON_MINOR      0x0001

// TX Power: calibrated measured RSSI at 1 metre
// -59 dBm is typical. Increase for wider range, decrease for tighter proximity.
#define TX_POWER          -59

// RSSI threshold hint stored in beacon metadata
// Flutter compares scanned RSSI against this value
// -70 dBm means student must be within ~5 metres
#define RSSI_THRESHOLD    -70

// BLE advertising interval (milliseconds)
// Lower = faster detection, higher battery drain
#define ADVERTISE_INTERVAL_MS  100

// LED blink config
#define LED_PIN           2      // GPIO2 = built-in LED on most ESP32 DevKit
#define LED_ON_MS         50     // blink duration
#define LED_PERIOD_MS     2000   // blink every N ms

// Deep sleep config (optional power saving — disabled by default)
#define ENABLE_DEEP_SLEEP false
#define AWAKE_SECONDS     30     // advertise for this long before sleeping
#define SLEEP_SECONDS     5      // sleep duration

// ─────────────────────────────────────────────────────────────────────────────
// GLOBALS
// ─────────────────────────────────────────────────────────────────────────────
BLEAdvertising* pAdvertising = nullptr;
unsigned long lastLedBlink   = 0;
unsigned long startTime      = 0;
bool ledState                = false;


// ─────────────────────────────────────────────────────────────────────────────
// Helper: configure iBeacon advertising payload
// ─────────────────────────────────────────────────────────────────────────────
void configureBeaconAdvertising() {
  BLEBeacon beacon;
  beacon.setManufacturerId(0x004C);  // Apple iBeacon manufacturer ID
  beacon.setProximityUUID(BLEUUID(BEACON_UUID));
  beacon.setMajor(BEACON_MAJOR);
  beacon.setMinor(BEACON_MINOR);
  beacon.setSignalPower(TX_POWER);

  BLEAdvertisementData oAdvertisementData;
  oAdvertisementData.setFlags(0x04);  // BR_EDR_NOT_SUPPORTED

  std::string strServiceData = "";
  strServiceData += (char)26;      // Beacon data length
  strServiceData += (char)0xFF;    // Type: Manufacturer Specific
  strServiceData += beacon.getData();
  oAdvertisementData.addData(strServiceData);

  // Scan response includes device name for flutter_blue_plus name filtering
  BLEAdvertisementData oScanResponseData;
  oScanResponseData.setCompleteLocalName(DEVICE_NAME);
  // Embed RSSI threshold hint as service data (0xFEED = SmartAttend custom UUID)
  // Format: 2-byte RSSI threshold as signed int16
  std::string rssiHint = "";
  rssiHint += (char)0x05;          // Length of service data field
  rssiHint += (char)0x16;          // Type: Service Data
  rssiHint += (char)0xED;          // UUID low byte (0xFEED)
  rssiHint += (char)0xFE;          // UUID high byte
  rssiHint += (char)(RSSI_THRESHOLD & 0xFF);
  rssiHint += (char)((RSSI_THRESHOLD >> 8) & 0xFF);
  oScanResponseData.addData(rssiHint);

  pAdvertising->setAdvertisementData(oAdvertisementData);
  pAdvertising->setScanResponseData(oScanResponseData);
}


// ─────────────────────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("");
  Serial.println("╔══════════════════════════════════════════╗");
  Serial.println("║       SmartAttend AI — BLE Beacon        ║");
  Serial.println("╠══════════════════════════════════════════╣");
  Serial.print  ("║  Room:     "); Serial.println(ROOM_NAME);
  Serial.print  ("║  Device:   "); Serial.println(DEVICE_NAME);
  Serial.print  ("║  UUID:     "); Serial.println(BEACON_UUID);
  Serial.print  ("║  RSSI Threshold: "); Serial.println(RSSI_THRESHOLD);
  Serial.println("╚══════════════════════════════════════════╝");

  // LED setup
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // BLE init
  BLEDevice::init(DEVICE_NAME);
  BLEDevice::setPower(ESP_PWR_LVL_P7);  // Max TX power (+7 dBm)

  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->setMinInterval(ADVERTISE_INTERVAL_MS * 1.6);  // Units: 0.625ms
  pAdvertising->setMaxInterval(ADVERTISE_INTERVAL_MS * 1.6 + 10);

  configureBeaconAdvertising();
  pAdvertising->start();

  Serial.println("[BLE] ✅ Beacon advertising started.");
  Serial.print("[BLE]    Advertising as: "); Serial.println(DEVICE_NAME);

  startTime = millis();
}


// ─────────────────────────────────────────────────────────────────────────────
// LOOP
// ─────────────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // ── LED heartbeat blink ────────────────────────────────────────────────────
  if (now - lastLedBlink >= (unsigned long)(ledState ? LED_ON_MS : (LED_PERIOD_MS - LED_ON_MS))) {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    lastLedBlink = now;
  }

  // ── Optional deep-sleep cycle ──────────────────────────────────────────────
  if (ENABLE_DEEP_SLEEP) {
    if (now - startTime >= (unsigned long)(AWAKE_SECONDS * 1000)) {
      Serial.println("[POWER] Going to deep sleep for " + String(SLEEP_SECONDS) + "s...");
      pAdvertising->stop();
      digitalWrite(LED_PIN, LOW);
      esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_SECONDS * 1000000ULL);
      esp_deep_sleep_start();
    }
  }

  // ── Serial command handler ─────────────────────────────────────────────────
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "status") {
      Serial.println("[STATUS] Advertising: " + String(pAdvertising ? "YES" : "NO"));
      Serial.println("[STATUS] Uptime: " + String(millis() / 1000) + "s");
      Serial.println("[STATUS] Room: " + String(ROOM_NAME));
      Serial.println("[STATUS] UUID: " + String(BEACON_UUID));
    } else if (cmd == "restart") {
      Serial.println("[CMD] Restarting...");
      ESP.restart();
    } else {
      Serial.println("[CMD] Unknown. Try: status | restart");
    }
  }

  delay(10);  // Yield to RTOS scheduler
}
