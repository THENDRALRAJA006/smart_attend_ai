/*
  SmartAttend AI - BLE Proximity Advertising Beacon for ESP32
  
  This firmware configures an ESP32 device to act as an iBeacon/Custom BLE advertiser.
  The mobile application scans for this beacon to verify the student is physically present 
  inside the correct classroom room before initiating liveness and face verification checks.
*/

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>

// --- Configuration Definitions ---
#define ROOM_NAME "SMARTATTEND_ROOM101"                 // Device name filtered by Flutter app
#define BEACON_UUID "fda50693-a4e2-4fb1-afcf-c6eb07647825" // Unique Identifier matching DB ble_beacons table

#define LED_PIN 2            // Status LED (Blinks on startup / advertising cycle)
#define ADVERTISE_INTERVAL_MS 100 // Fast advertising rate for quick device discovery

BLEAdvertising *pAdvertising;

void setup() {
  Serial.begin(115200);
  Serial.println("SmartAttend AI: Starting BLE Beacon initialization...");

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn LED on during boot

  // 1. Initialize the BLE Device
  BLEDevice::init(ROOM_NAME);

  // 2. Create the BLE Server
  BLEServer *pServer = BLEDevice::createServer();

  // 3. Create advertising object
  pAdvertising = BLEDevice::getAdvertising();
  
  // 4. Create and configure iBeacon data structure
  BLEBeacon oBeacon = BLEBeacon();
  oBeacon.setManufacturerId(0x4C00); // Apple Manufacturer ID for standard beacon setups
  oBeacon.setProximityUUID(BLEUUID(BEACON_UUID));
  oBeacon.setMajor(1);
  oBeacon.setMinor(1);
  oBeacon.setSignalPower(-59); // Calibrated TX RSSI at 1 meter distance

  // 5. Structure BLE advertisement payload
  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  oAdvertisementData.setFlags(0x04); // BR_EDR_NOT_SUPPORTED
  
  // Set manufacturer data containing the iBeacon properties
  std::string strServiceData = "";
  strServiceData += (char)26;     // Len
  strServiceData += (char)0xFF;   // Type (Manufacturer Specific Data)
  strServiceData += oBeacon.getData();
  oAdvertisementData.setManufacturerData(strServiceData);
  
  // Set advertising name explicitly so app filters it correctly
  BLEAdvertisementData oScanResponseData = BLEAdvertisementData();
  oScanResponseData.setName(ROOM_NAME);
  
  pAdvertising->setAdvertisementData(oAdvertisementData);
  pAdvertising->setScanResponseData(oScanResponseData);

  // 6. Tune TX Power settings for stable RSSI readings
  // ESP32 supports power levels: ESP_PWR_LVL_M12, ESP_PWR_LVL_M9, ESP_PWR_LVL_M6, ESP_PWR_LVL_M3, 
  // ESP_PWR_LVL_N0, ESP_PWR_LVL_P3, ESP_PWR_LVL_P6, ESP_PWR_LVL_P9
  esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P9); // Maximum range TX
  esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_P9);

  // Set advertisement interval
  pAdvertising->setMinInterval(ADVERTISE_INTERVAL_MS / 0.625);
  pAdvertising->setMaxInterval(ADVERTISE_INTERVAL_MS / 0.625);

  // 7. Start advertising
  pAdvertising->start();
  Serial.print("BLE Advertising started. Device Local Name: ");
  Serial.println(ROOM_NAME);
  Serial.print("Beacon Service UUID: ");
  Serial.println(BEACON_UUID);

  digitalWrite(LED_PIN, LOW); // Initial boot complete
}

void loop() {
  // Beacon loops and advertises in the background.
  // LED blinks periodically to indicate advertising heartbeats.
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  delay(900);
}
