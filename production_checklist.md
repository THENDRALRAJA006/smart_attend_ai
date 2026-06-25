# SmartAttend AI — Production Deployment Checklist

## Pre-Deployment

### 🗄️ AWS RDS MySQL Setup
- [ ] Create RDS MySQL 8.0 instance (db.t3.medium or higher recommended)
- [ ] Set DB identifier: `smartattend-db`
- [ ] Create database: `CREATE DATABASE smartattend CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
- [ ] Create DB user with limited privileges:
  ```sql
  CREATE USER 'smartattend_user'@'%' IDENTIFIED BY 'strong-password-here';
  GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON smartattend.* TO 'smartattend_user'@'%';
  FLUSH PRIVILEGES;
  ```
- [ ] RDS Security Group: allow TCP port 3306 from Render IP ranges
  - Render CIDR ranges: check https://render.com/docs/static-outbound-ip-addresses
- [ ] Test connection string from a local machine:
  ```bash
  mysql -h your-endpoint.rds.amazonaws.com -u smartattend_user -p smartattend
  ```
- [ ] Set `DATABASE_URL` in Render environment:
  ```
  mysql+pymysql://smartattend_user:password@your-endpoint.rds.amazonaws.com:3306/smartattend?charset=utf8mb4
  ```

### 🔑 JWT Security
- [ ] `JWT_SECRET` is cryptographically random (≥ 32 characters):
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] JWT_SECRET is set as an environment variable — NOT hardcoded
- [ ] Student/Faculty tokens expire in 24 hours (admin: 8 hours)
- [ ] `JWT_ALGORITHM` = `HS256`

### 🤖 AI Models
- [ ] ArcFace `buffalo_l` model downloaded and cached during Docker build step
- [ ] DeepFace `Emotion` model pre-cached during Docker build step
- [ ] Model cache persists across Render deploys (use persistent disk if needed)
- [ ] Verify in Dockerfile: build-time `python -c "from insightface.app import FaceAnalysis..."` succeeds
- [ ] `ARCFACE_MODEL_NAME=buffalo_l` set in environment

### 🗃️ Database Migration
- [ ] Run Alembic migrations before first deploy:
  ```bash
  cd smartattend_backend
  alembic upgrade head
  ```
- [ ] Verify all tables created:
  ```sql
  SHOW TABLES;
  -- Expected: students, faculty, admins, subjects, classrooms, ble_beacons,
  --           attendance_sessions, face_embeddings, attendance, liveness_tokens
  ```
- [ ] Seed data migration (002) executed successfully
- [ ] Default admin credentials created: `admin@smartattend.ai` / `Admin@2026`
- [ ] **CHANGE DEFAULT ADMIN PASSWORD** before going live

---

## Backend Security

### 🔐 Authentication
- [ ] All endpoints (except `/auth/*` and `/health`) require valid JWT
- [ ] Role-based access: `student` / `faculty` / `admin` claims in JWT
- [ ] Liveness tokens are UUID v4, single-use, expire in 3 minutes
- [ ] Liveness token validated before any face verification
- [ ] Rate limiting: max `MAX_VERIFICATION_ATTEMPTS` (default: 5) per student per session

### 🛡️ Anti-Proxy Protection
- [ ] UNIQUE constraint on `(student_id, session_id)` in `attendance` table verified
- [ ] Liveness challenge required before every selfie submission
- [ ] `is_used = true` set atomically on liveness token consumption
- [ ] ArcFace similarity thresholds configured:
  - `SIMILARITY_THRESHOLD_PRESENT=0.75` (confident match → present)
  - `SIMILARITY_THRESHOLD_REVIEW=0.65` (borderline → manual review)
  - Below 0.65 → rejected

### 📷 Image Data Policy
- [ ] Raw image frames NEVER written to disk (in-memory only)
- [ ] Only 512-dim float32 embeddings stored in `face_embeddings.embedding_json`
- [ ] LONGTEXT column verified for `embedding_json` (MySQL)
- [ ] No S3/storage bucket configured (intentional — embeddings only)

### 🌐 Network
- [ ] HTTPS only (Render provides TLS — no custom cert needed)
- [ ] CORS origins restricted for production (update `allow_origins` in main.py)
- [ ] Database not publicly accessible (RDS in private subnet with security group)

---

## Face Registration Quality

- [ ] `MIN_FRAMES_FOR_REGISTRATION=20` enforced (recommended: 100–150 frames sent)
- [ ] `SHARPNESS_THRESHOLD=100.0` (Laplacian variance filter)
- [ ] `DETECTION_CONFIDENCE_THRESHOLD=0.95` (ArcFace detector confidence)
- [ ] `DEDUP_SIMILARITY_THRESHOLD=0.98` (cosine similarity deduplication)
- [ ] `MAX_FACE_EMBEDDINGS=50` embeddings stored per student
- [ ] Registration covers all 15 guided poses for diversity
- [ ] Students re-register if embeddings count < 15

---

## ESP32 BLE Beacons

- [ ] Device name format: `SMARTATTEND_<ROOM_NAME>` (must start with `SMARTATTEND_`)
- [ ] Unique UUID per beacon/room (`BEACON_UUID` in .ino file)
- [ ] RSSI threshold calibrated per room (measure at typical student sitting distance)
  - Recommended: -65 dBm to -75 dBm depending on room size
- [ ] `RSSI_THRESHOLD` set correctly in both ESP32 firmware and DB (`ble_beacons.rssi_threshold`)
- [ ] Beacon UUID registered in DB via `POST /admin/beacons`
- [ ] Beacon device name linked to classroom via `classroom_id` in DB
- [ ] TX power set to `ESP_PWR_LVL_P7` (+7 dBm) for classroom-scale range
- [ ] Advertising interval: 100ms for fast Flutter detection

---

## Flutter App

### Android
- [ ] `AndroidManifest.xml` Bluetooth permissions:
  ```xml
  <uses-permission android:name="android.permission.BLUETOOTH_SCAN"
      android:usesPermissionFlags="neverForLocation" />
  <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-feature android:name="android.hardware.bluetooth_le" android:required="true" />
  ```
- [ ] `minSdkVersion` ≥ 21 (BLE required)
- [ ] Tested on Android 10, 12, 14

### iOS
- [ ] `Info.plist` keys:
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>Camera is used for face registration and liveness verification</string>
  <key>NSBluetoothAlwaysUsageDescription</key>
  <string>Bluetooth is used to detect classroom proximity beacons</string>
  <key>NSBluetoothPeripheralUsageDescription</key>
  <string>Bluetooth proximity is used to verify classroom attendance</string>
  <key>NSLocationWhenInUseUsageDescription</key>
  <string>Location is required for BLE scanning on iOS</string>
  ```
- [ ] Tested on iOS 14, 16, 17

### App Configuration
- [ ] `ApiConstants.baseUrl` set to production Render URL
- [ ] SSL/TLS connection working (Render provides HTTPS)
- [ ] JWT stored in `flutter_secure_storage` (never in SharedPreferences)
- [x] Camera permission requested at runtime
- [ ] BLE permission requested at runtime

---

## Render Deployment

- [ ] Docker build succeeds locally:
  ```bash
  docker build -t smartattend-backend ./smartattend_backend
  docker run -p 8000:8000 --env-file smartattend_backend/.env smartattend-backend
  ```
- [ ] Health check passes: `GET /health` returns `{"status": "ok"}`
- [ ] Database connection verified on startup (check Render logs)
- [ ] AI models pre-cached in image (verify in build logs)
- [ ] `render.yaml` deployed with correct `DATABASE_URL`
- [ ] Render deploy hook runs `alembic upgrade head` before server start
- [ ] Minimum plan: **Standard** (AI models require >512MB RAM)

---

## Monitoring & Operations

- [ ] Set up Render alerts for deploy failures
- [ ] Monitor RDS CloudWatch for connection count spikes
- [ ] Liveness token cleanup job (delete expired tokens):
  ```sql
  DELETE FROM liveness_tokens WHERE expires_at < NOW() - INTERVAL 1 HOUR;
  ```
  Schedule as a cron job (MySQL Event Scheduler or AWS Lambda)
- [ ] Face embedding backup strategy documented
- [ ] Admin password rotation policy defined

---

## Default Credentials (CHANGE BEFORE GO-LIVE!)

| Role    | Email                      | Password      |
|---------|----------------------------|---------------|
| Admin   | admin@smartattend.ai       | Admin@2026    |
| Faculty | faculty@smartattend.ai     | Faculty@123   |
| Student | (self-registered)          | (user-chosen) |

> ⚠️ **CRITICAL**: Change all default credentials immediately after first deployment.

---

## Alembic Migration Commands

```bash
cd smartattend_backend

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run all migrations
alembic upgrade head

# Check current revision
alembic current

# View migration history
alembic history

# Rollback one step (if needed)
alembic downgrade -1
```

---

## AWS RDS Parameter Group (MySQL 8.0)

Recommended parameter overrides for production:

| Parameter                    | Value        | Notes                        |
|------------------------------|--------------|------------------------------|
| `max_connections`            | 200          | Increase for scale           |
| `innodb_buffer_pool_size`    | 75% of RAM   | Memory-optimized             |
| `character_set_server`       | utf8mb4      | Full Unicode support         |
| `collation_server`           | utf8mb4_unicode_ci | Consistent collation  |
| `wait_timeout`               | 28800        | 8h (keep alive)              |
| `interactive_timeout`        | 28800        | 8h                           |
| `max_allowed_packet`         | 67108864     | 64MB for large embedding JSON |
| `innodb_lock_wait_timeout`   | 50           | Prevent deadlock hangs       |
