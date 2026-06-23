# Production Deployment Checklist - SmartAttend AI

This checklist outlines the critical verification points for pushing SmartAttend AI to commercial production. Ensure all checkboxes are validated prior to deployment.

## 1. Machine Learning & Face Analysis
- [ ] **ArcFace Weights Cached**: Buffalo_l model weights are successfully downloaded and cached into the Docker image during the build stage (minimizes cold-start latency).
- [ ] **Emotion Models Cached**: DeepFace emotion recognition models are cached in `/root/.deepface/` during the build stage.
- [ ] **No Image Persistence**: Confirmed that no raw byte streams or image frames are written to local disk or logs at any point. Only 512-dimension vector embeddings are kept.

## 2. Infrastructure & Hosting
- [ ] **RDS Connectivity**: AWS Aurora PostgreSQL instance is accessible from the Render deployment web service IPs (verify inbound security group rules on port 5432).
- [ ] **PostgreSQL Driver Translation**: The `DATABASE_URL` resolves to `postgresql+psycopg2://` driver (translated dynamically by `config.py`).
- [ ] **Alembic Database Seed**: Alembic migrations have been successfully executed (`alembic upgrade head`) to seed initial faculty, classrooms, beacons, and sessions.
- [ ] **HTTPS Enforced**: Render-provided SSL/TLS is active, and all communication uses `https://` protocols.

## 3. Backend & Security
- [ ] **Cryptographically Secure Secrets**: `JWT_SECRET` in environment settings is configured to a random 64-character hex sequence.
- [ ] **Token Expirations**: JWT tokens expire in 24 hours for students/faculty and 8 hours for administrators.
- [ ] **Single-Use Liveness Tokens**: Verify that secondary liveness verification tokens are flagged as `is_used` in the database immediately upon the first attendance check.
- [ ] **Rate Limiting**: Rate-limiting cache blocks students after 5 face comparison attempts per classroom session.
- [ ] **Unique Constraints**: Unique constraint index verified on database table `attendance(student_id, session_id)` to prevent double-marking proxy attendance.

## 4. Hardware & Proximity
- [ ] **ESP32 BLE Calibration**: RSSI signal strength threshold calibrated for each room (measure RSSI from the furthest corner of the classroom to set `rssi_threshold` accurately, typical range is `-70` to `-80` dBm).
- [ ] **Beacon UUID Sync**: Confirm that UUIDs advertised in the ESP32 code align exactly with values in the `ble_beacons` table.

## 5. Mobile Client (Flutter)
- [ ] **Android Permissions**: `AndroidManifest.xml` includes camera and BLE hardware permissions:
  ```xml
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
  <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
  ```
- [ ] **iOS Permissions**: `Info.plist` contains usage explanation tags for camera, bluetooth, and location:
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>SmartAttend AI requires camera access for guided pose capture and identity verification.</string>
  <key>NSBluetoothAlwaysUsageDescription</key>
  <string>SmartAttend AI requires bluetooth scanning to verify student proximity to the classroom beacon.</string>
  <key>NSLocationWhenInUseUsageDescription</key>
  <string>SmartAttend AI requires location access to find nearby BLE beacons.</string>
  ```
- [ ] **Dio Endpoint Mapping**: `ApiConstants.baseUrl` is updated from the localhost emulator mapping (`http://10.0.2.2:8000`) to the active production web service address.
