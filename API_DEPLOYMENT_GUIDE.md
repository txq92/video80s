# 🚀 Video80s API Deployment Guide

Hướng dẫn deploy hệ thống Web API hoàn chỉnh với Docker Compose.

## 📋 Tổng quan hệ thống

### 🎯 **Các tính năng chính:**
- ✅ **Web Dashboard** - Giao diện quản lý trực quan
- ✅ **Video Processing API** - Upload và xử lý video (resize 9:16, logo, banner)
- ✅ **Direct YouTube Upload API** - Upload trực tiếp lên YouTube
- ✅ **Job Tracking** - Theo dõi tiến trình real-time
- ✅ **File Management** - Download video đã xử lý
- ✅ **REST API** - Tích hợp với ứng dụng khác

### 🏗️ **Kiến trúc:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Flask API     │    │   File Storage  │
│   (Port 80)     │────│   (Port 5000)   │────│   (Volumes)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │  YouTube API    │
                       │  (OAuth 2.0)    │
                       └─────────────────┘
```

## 🛠️ Cách deploy

### **Method 1: Docker Compose (Recommended)**

#### **1. Chuẩn bị:**
```bash
# Install Docker và Docker Compose
# Windows: Docker Desktop
# Linux: 
sudo apt update && sudo apt install docker.io docker-compose

# Kiểm tra
docker --version
docker-compose --version
```

#### **2. Setup credentials:**
```bash
# Đảm bảo có file Google OAuth
ls -la client_secrets.json token.pickle

# Nếu chưa có, chạy setup trước
python check_credentials.py
```

#### **3. Deploy với Docker:**
```bash
# Build và start services
docker-compose up -d

# Xem logs
docker-compose logs -f video80s-api

# Check status
docker-compose ps
```

#### **4. Truy cập:**
- **Web Interface**: http://localhost:5000
- **API Docs**: http://localhost:5000/api/health
- **With Nginx**: http://localhost (nếu enable nginx profile)

### **Method 2: Local Development**

#### **1. Install dependencies:**
```bash
# Install Python packages
pip install -r requirements_api.txt

# Trên Ubuntu/Debian
sudo apt install ffmpeg

# Trên macOS
brew install ffmpeg
```

#### **2. Run server:**
```bash
python app.py
```

#### **3. Truy cập:**
- **Web Interface**: http://localhost:5000

## 📱 Cách sử dụng Web Interface

### **1. Dashboard (http://localhost:5000)**
- Xem tổng quan: videos processed, uploads, jobs running
- Recent jobs và system status
- Quick actions: Process Video, Direct Upload

### **2. Process Video (http://localhost:5000/upload)**
- Upload video để xử lý
- Chọn background style: Blur, Gradient, Solid
- Option: Auto upload lên YouTube sau khi xử lý
- Real-time progress tracking
- Download processed video

### **3. Direct Upload (http://localhost:5000/direct-upload)**
- Upload video trực tiếp lên YouTube
- Custom title, description, tags
- Privacy settings: Public, Unlisted, Private
- Auto-detect YouTube Shorts format

### **4. Job Status (http://localhost:5000/status)**
- Theo dõi tất cả jobs
- Filter theo status, type, filename
- View job details
- Download results, view YouTube links

## 🔧 API Endpoints

### **Health Check**
```bash
GET /api/health
```

### **Process Video**
```bash
POST /api/process-video
Content-Type: multipart/form-data

Body:
- video: (file) Video file
- background_style: blur|gradient|solid
- auto_upload: true|false

Response:
{
  "job_id": "uuid",
  "status": "accepted",
  "message": "Video processing started"
}
```

### **Direct Upload**
```bash
POST /api/direct-upload
Content-Type: multipart/form-data

Body:
- video: (file) Video file
- title: (string) Video title
- description: (string) Description
- tags: (string) Comma-separated tags
- privacy: public|unlisted|private

Response:
{
  "job_id": "uuid",
  "status": "accepted",
  "message": "Upload started"
}
```

### **Job Status**
```bash
GET /api/job/{job_id}

Response:
{
  "id": "uuid",
  "status": "pending|processing|completed|failed",
  "progress": 0-100,
  "message": "Current status message",
  "result": { /* Upload/processing result */ }
}
```

### **List All Jobs**
```bash
GET /api/jobs

Response:
{
  "process_uuid1": { /* Processing job */ },
  "upload_uuid2": { /* Upload job */ }
}
```

### **Download Processed Video**
```bash
GET /api/download/{filename}
```

### **List Available Files**
```bash
GET /api/files

Response:
[
  {
    "filename": "processed_video.mp4",
    "size": 12345678,
    "modified": "2025-01-01T12:00:00",
    "download_url": "/api/download/processed_video.mp4"
  }
]
```

## 🐳 Docker Compose Profiles

### **Basic (Default)**
```bash
docker-compose up -d
# Chỉ chạy video80s-api
```

### **With Nginx Reverse Proxy**
```bash
docker-compose --profile production up -d
# Chạy video80s-api + nginx
# Truy cập: http://localhost
```

### **With Monitoring**
```bash
docker-compose --profile monitoring up -d
# Chạy thêm Prometheus + Grafana
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

### **Full Stack**
```bash
docker-compose --profile production --profile monitoring up -d
# Chạy tất cả services
```

## ⚙️ Configuration

### **Environment Variables**
Chỉnh sửa trong `docker-compose.yml`:
```yaml
environment:
  - DEFAULT_LOGO_PATH=/app/assets/logo.png
  - DEFAULT_BANNER_PATH=/app/assets/banner.png
  - BACKGROUND_STYLE=blur
  - DATABASE_FILE=/app/data/videos_database.json
```

### **Resource Limits**
Adjust trong `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

### **Nginx Configuration**
Chỉnh sửa `nginx.conf` để:
- Thay đổi rate limiting
- Add SSL certificates
- Custom error pages

## 🔒 Security Best Practices

### **1. Protect Credentials**
```bash
# Set proper permissions
chmod 600 client_secrets.json token.pickle

# Không commit credentials vào git
echo "client_secrets.json" >> .gitignore
echo "token.pickle" >> .gitignore
```

### **2. Network Security**
```bash
# Chỉ expose cần thiết ports
# Use nginx as reverse proxy
# Enable rate limiting
```

### **3. HTTPS/SSL**
```bash
# Uncomment HTTPS server trong nginx.conf
# Add SSL certificates vào ssl/ directory
# Update docker-compose volumes
```

## 🚨 Troubleshooting

### **1. Container không start**
```bash
docker-compose logs video80s-api
# Check logs for errors

# Common issues:
# - Missing client_secrets.json
# - Port 5000 already in use
# - Insufficient disk space
```

### **2. Upload fails**
```bash
# Check credentials
python check_credentials.py

# Check YouTube API quota
# https://console.cloud.google.com/

# Check container resources
docker stats
```

### **3. Video processing slow**
```bash
# Increase container resources
# Check ffmpeg installation
docker exec video80s-api ffmpeg -version
```

## 📊 Monitoring & Logs

### **Application Logs**
```bash
# Real-time logs
docker-compose logs -f video80s-api

# Specific timeframe
docker-compose logs --since="1h" video80s-api
```

### **System Metrics**
```bash
# Container stats
docker stats

# With Grafana (if enabled)
# http://localhost:3000
# Import dashboard for Docker containers
```

### **Health Checks**
```bash
# API health
curl http://localhost:5000/api/health

# Container health
docker-compose ps
```

## 🔄 Backup & Restore

### **Backup Important Data**
```bash
# Backup data directory
tar -czf video80s-backup-$(date +%Y%m%d).tar.gz \
    data/ output/ assets/ client_secrets.json token.pickle

# Automated backup script
# (Add to crontab)
```

### **Restore**
```bash
# Stop services
docker-compose down

# Restore data
tar -xzf video80s-backup-20250101.tar.gz

# Start services
docker-compose up -d
```

## 🚀 Production Deployment

### **1. Server Requirements**
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended  
- **Storage**: 50GB+ for video files
- **Network**: Upload bandwidth cho YouTube

### **2. Domain Setup**
```bash
# Update nginx.conf
server_name yourdomain.com;

# SSL certificates (Let's Encrypt)
certbot --nginx -d yourdomain.com
```

### **3. Process Management**
```bash
# Auto-start on boot
docker-compose up -d --restart unless-stopped

# Process monitoring
# Add to systemd or use process manager
```

---

## 🎯 Quick Start Commands

```bash
# 1. Clone hoặc setup project
cd video80s/

# 2. Setup credentials (one time)
python check_credentials.py

# 3. Start development
python app.py
# Hoặc start production
docker-compose up -d

# 4. Access web interface
open http://localhost:5000
```

**🎉 Enjoy your Video80s API system!**