# Hướng Dẫn Setup YouTube API

## Vấn đề: Video không tự động tải lên YouTube

Nếu bạn gặp lỗi video không tự động tải lên YouTube sau khi xử lý, nguyên nhân chính là **chưa setup YouTube API credentials**.

## Giải pháp: Setup YouTube API

### Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Enable **YouTube Data API v3**:
   - Vào **APIs & Services** → **Library**
   - Tìm "YouTube Data API v3"
   - Nhấn **Enable**

### Bước 2: Tạo OAuth 2.0 Credentials

1. Vào **APIs & Services** → **Credentials**
2. Nhấn **Create Credentials** → **OAuth 2.0 Client IDs**
3. Chọn **Application type**: Desktop application
4. Đặt tên: `Video80s YouTube Uploader`
5. Nhấn **Create**
6. **Download** file JSON credentials

### Bước 3: Setup Credentials trong Project

1. Đổi tên file JSON đã download thành `client_secrets.json`
2. Copy file này vào thư mục gốc của project (`C:\Users\chaut\video80s\`)
3. Cấu trúc file sẽ như sau:

```
video80s/
├── client_secrets.json    ← File này
├── app.py
├── config.py
└── ...
```

### Bước 4: Xác thực lần đầu

1. Chạy script test authentication:

```bash
python check_credentials.py
```

2. Lần đầu chạy sẽ mở browser để bạn đăng nhập Google
3. Chọn tài khoản YouTube bạn muốn upload
4. Chấp nhận quyền truy cập
5. Script sẽ tạo file `token.pickle` để lưu credentials

### Bước 5: Test Auto Upload

1. Mở web interface: `http://localhost:5000`
2. Vào **Process Video**
3. Upload một video test
4. ✅ **Bật checkbox "Auto upload to YouTube after processing"**
5. Nhấn **Start Processing**

## Cấu trúc Files sau khi Setup

```
video80s/
├── client_secrets.json    ← Google OAuth credentials
├── token.pickle          ← Saved authentication token (tự động tạo)
├── app.py
├── config.py
└── ...
```

## Kiểm tra Setup

Chạy lệnh sau để kiểm tra credentials:

```bash
python -c "from src.youtube_uploader import YouTubeUploader; u = YouTubeUploader(); print('✅ YouTube API setup thành công!' if u.youtube else '❌ Chưa setup đúng')"
```

## Troubleshooting

### Lỗi "No client_secrets.json found"
- Đảm bảo file `client_secrets.json` nằm trong thư mục gốc
- Kiểm tra tên file không bị sai chính tả

### Lỗi "Authentication failed"
- Xóa file `token.pickle` và authenticate lại
- Kiểm tra OAuth 2.0 credentials có được enable chưa
- Đảm bảo YouTube Data API v3 đã được enable

### Video upload thành công nhưng không hiển thị link
- Kiểm tra console logs để xem có lỗi gì
- Đảm bảo account YouTube có quyền upload

## Lưu ý bảo mật

- **KHÔNG** commit `client_secrets.json` vào Git
- **KHÔNG** chia sẻ `token.pickle` với người khác
- Thêm vào `.gitignore`:

```
client_secrets.json
token.pickle
*.pickle
```

---

**Sau khi setup xong, chức năng "Auto upload to YouTube" sẽ hoạt động bình thường! 🎉**