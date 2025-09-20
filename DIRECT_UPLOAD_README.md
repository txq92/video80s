# 📤 Direct YouTube Upload Features

Đã thêm chức năng upload video trực tiếp lên YouTube **không cần edit** để tiết kiệm thời gian.

## 🚀 3 Cách Upload Trực Tiếp

### 1. **Quick Upload** - Upload nhanh nhất
```bash
# Upload 1 video với title tự động
python quick_upload.py input/video.mp4

# Upload với custom title
python quick_upload.py input/video.mp4 "Tiêu đề video của tôi"
```

### 2. **Direct Upload** - Đầy đủ tùy chọn
```bash
# Upload đơn giản
python direct_upload.py input/video.mp4

# Upload với metadata chi tiết
python direct_upload.py input/video.mp4 \
  --title "Video hay" \
  --description "Mô tả video" \
  --tags "gaming,funny,vietnam" \
  --privacy public \
  --thumbnail thumb.jpg

# Upload toàn bộ folder
python direct_upload.py --folder input/ --privacy unlisted

# Upload với metadata file
python direct_upload.py --folder input/ --metadata video_info.json
```

### 3. **Integrated với Main** - Từ main.py
```bash
# Upload trực tiếp thay vì edit
python main.py input/video.mp4 --direct-upload
```

## 📋 Metadata File Support

### Tạo template metadata:
```bash
python direct_upload.py --create-template
```

### Chỉnh sửa `video_metadata_template.json`:
```json
{
  "video1.mp4": {
    "title": "Video số 1",
    "description": "Mô tả chi tiết\n\n#Hashtags #YouTube",
    "tags": ["gaming", "funny", "vietnam"],
    "privacy": "public",
    "category_id": "22"
  },
  "video2.mp4": {
    "title": "Video số 2",
    "description": "Video khác",
    "tags": ["entertainment"],
    "privacy": "unlisted"
  }
}
```

### Sử dụng metadata:
```bash
python direct_upload.py --folder input/ --metadata video_info.json
```

## 🎯 YouTube Category IDs

| ID | Category | Mô tả |
|----|----------|-------|
| 1  | Film & Animation | Phim và Hoạt hình |
| 2  | Autos & Vehicles | Xe cộ |
| 10 | Music | Âm nhạc |
| 15 | Pets & Animals | Thú cưng |
| 17 | Sports | Thể thao |
| 19 | Travel & Events | Du lịch |
| 20 | Gaming | Game |
| 22 | People & Blogs | Con người (mặc định) |
| 23 | Comedy | Hài kịch |
| 24 | Entertainment | Giải trí |
| 25 | News & Politics | Tin tức |
| 26 | Howto & Style | Hướng dẫn |
| 27 | Education | Giáo dục |
| 28 | Science & Technology | Khoa học |

## 📊 Tính Năng Chính

### ✅ Quick Upload (`quick_upload.py`)
- Upload siêu nhanh với minimal setup
- Auto-generate title từ filename
- Suitable cho upload đơn giản

### ✅ Direct Upload (`direct_upload.py`)
- Full customization: title, description, tags, privacy
- Batch upload từ folder
- Metadata file support
- Upload log tracking
- File size warnings
- Progress tracking

### ✅ Main Integration
- Thêm `--direct-upload` flag vào `main.py`
- Seamless integration với workflow hiện tại

## 🔒 Privacy Settings
- `public` - Công khai (mặc định)
- `unlisted` - Không công khai (chỉ ai có link)
- `private` - Riêng tư (chỉ mình xem)

## 📝 Upload Logs
Thông tin upload được lưu tự động vào:
```
logs/direct_uploads.json
```

Chứa: video ID, URL, Shorts URL, file size, timestamp, etc.

## 🎯 Ví Dụ Workflow

### Upload 1 video nhanh:
```bash
python quick_upload.py "Tên Chiến Trận Không.mp4"
```

### Upload nhiều video với metadata:
```bash
# 1. Tạo template
python direct_upload.py --create-template

# 2. Chỉnh sửa metadata file
# 3. Upload
python direct_upload.py --folder input/ --metadata video_metadata_template.json
```

### Upload folder với filter:
```bash
# Chỉ upload .mp4 và .mov
python direct_upload.py --folder input/ --filter-ext mp4,mov --privacy unlisted
```

## 🔧 Setup Requirements

Đảm bảo có:
1. ✅ `client_secrets.json` (từ Google Console)
2. ✅ `token.pickle` (tự tạo khi first run)
3. ✅ Internet connection

## 💡 Tips

1. **Batch Upload**: Có delay 15s giữa các video để tránh rate limit
2. **File Size**: Cảnh báo cho files > 2GB
3. **Authentication**: Hỗ trợ cả Windows và Linux
4. **Thumbnails**: Max 2MB, formats: JPG, PNG
5. **Progress**: Real-time upload progress tracking

---

**Chọn script phù hợp:**
- 🚀 **Quick**: `quick_upload.py` cho speed
- 🎛️ **Full**: `direct_upload.py` cho control
- 🔗 **Integrated**: `main.py --direct-upload` cho workflow