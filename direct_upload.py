#!/usr/bin/env python3
"""
Direct YouTube Upload - Upload video trực tiếp lên YouTube không cần edit
"""
import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Import module YouTube uploader
from src.youtube_uploader import YouTubeUploader
from config import YOUTUBE_CONFIG, setup_directories


def direct_upload_video(video_path, title=None, description=None, tags=None, 
                       privacy='public', thumbnail=None, category_id='22'):
    """
    Upload video trực tiếp lên YouTube mà không cần edit
    
    Args:
        video_path: Đường dẫn video cần upload
        title: Tiêu đề video (auto-generate nếu None)
        description: Mô tả video
        tags: List tags cho video
        privacy: 'public', 'private', 'unlisted'
        thumbnail: Đường dẫn thumbnail (optional)
        category_id: YouTube category ID
    
    Returns:
        Dict kết quả upload
    """
    print("=" * 60)
    print("📤 DIRECT YOUTUBE UPLOAD")
    print("=" * 60)
    
    # Kiểm tra file tồn tại
    if not os.path.exists(video_path):
        return {'status': 'error', 'message': f'File không tồn tại: {video_path}'}
    
    # Auto-generate title nếu không có
    if not title:
        filename = Path(video_path).stem
        title = f"{filename} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    # Default description
    if not description:
        description = f"""Video được upload trực tiếp từ file: {os.path.basename(video_path)}

Thời gian upload: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

#Video #YouTube"""
    
    # Default tags
    if not tags:
        tags = ['Video', 'Upload', 'Direct']
    
    # Hiển thị thông tin upload
    file_size = os.path.getsize(video_path)
    print(f"📁 File: {video_path}")
    print(f"📏 Size: {file_size / (1024*1024):.2f} MB")
    print(f"🏷️  Title: {title}")
    print(f"📝 Tags: {', '.join(tags)}")
    print(f"🔒 Privacy: {privacy}")
    if thumbnail:
        print(f"🖼️  Thumbnail: {thumbnail}")
    print("-" * 60)
    
    # Khởi tạo uploader
    try:
        uploader = YouTubeUploader(
            client_secrets_file=YOUTUBE_CONFIG['client_secrets_file'],
            credentials_file=YOUTUBE_CONFIG['credentials_file']
        )
    except Exception as e:
        return {'status': 'error', 'message': f'Lỗi khởi tạo uploader: {str(e)}'}
    
    # Thực hiện upload
    print("🚀 Bắt đầu upload...")
    result = uploader.upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        category_id=category_id,
        privacy_status=privacy,
        thumbnail_path=thumbnail
    )
    
    # Hiển thị kết quả
    print("\n" + "=" * 60)
    if result['status'] == 'success':
        print("✅ UPLOAD THÀNH CÔNG!")
        print(f"🆔 Video ID: {result['video_id']}")
        print(f"🔗 YouTube URL: {result['video_url']}")
        if 'shorts_url' in result:
            print(f"📱 Shorts URL: {result['shorts_url']}")
        print(f"📊 File size: {result.get('file_size', 0) / (1024*1024):.2f} MB")
        
        # Lưu link vào file log
        save_upload_log(result)
    else:
        print("❌ UPLOAD THẤT BẠI!")
        print(f"🔴 Lỗi: {result.get('message', 'Unknown error')}")
    
    print("=" * 60)
    return result


def upload_from_folder(folder_path, privacy='public', filter_ext=None):
    """
    Upload tất cả video trong folder
    
    Args:
        folder_path: Đường dẫn folder chứa video
        privacy: Privacy setting cho tất cả video
        filter_ext: List extension cần filter (None = all video formats)
    """
    if not os.path.exists(folder_path):
        print(f"❌ Folder không tồn tại: {folder_path}")
        return []
    
    # Default video extensions
    if not filter_ext:
        filter_ext = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.webm', '.flv']
    
    # Tìm tất cả video files
    video_files = []
    for file in os.listdir(folder_path):
        if any(file.lower().endswith(ext) for ext in filter_ext):
            video_files.append(os.path.join(folder_path, file))
    
    if not video_files:
        print(f"❌ Không tìm thấy video nào trong folder: {folder_path}")
        return []
    
    print(f"📂 Tìm thấy {len(video_files)} video trong folder")
    print("🕐 Bắt đầu upload batch...")
    
    results = []
    for i, video_path in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        
        result = direct_upload_video(
            video_path=video_path,
            privacy=privacy
        )
        results.append({
            'file': video_path,
            'result': result
        })
        
        # Delay giữa các upload
        if i < len(video_files):
            print("⏳ Đợi 15 giây trước video tiếp theo...")
            import time
            time.sleep(15)
    
    # Tổng kết
    success_count = sum(1 for r in results if r['result']['status'] == 'success')
    print(f"\n📊 TỔNG KẾT BATCH UPLOAD:")
    print(f"✅ Thành công: {success_count}/{len(results)}")
    print(f"❌ Thất bại: {len(results) - success_count}/{len(results)}")
    
    return results


def save_upload_log(result):
    """Lưu thông tin upload vào file log"""
    log_file = 'logs/direct_uploads.json'
    
    # Tạo folder logs nếu chưa có
    os.makedirs('logs', exist_ok=True)
    
    # Load existing data
    log_data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            log_data = []
    
    # Add new entry
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'video_id': result.get('video_id'),
        'title': result.get('title'),
        'video_url': result.get('video_url'),
        'shorts_url': result.get('shorts_url'),
        'file_size': result.get('file_size'),
        'privacy_status': result.get('privacy_status'),
        'tags': result.get('tags', [])
    }
    log_data.append(log_entry)
    
    # Save to file
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        print(f"📝 Đã lưu thông tin upload vào {log_file}")
    except Exception as e:
        print(f"⚠️  Không thể lưu log: {e}")


def load_metadata_from_file(metadata_file):
    """
    Load metadata cho video từ file JSON
    Format: {"filename.mp4": {"title": "...", "description": "...", "tags": [...]}}
    """
    if not os.path.exists(metadata_file):
        return {}
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Lỗi đọc metadata file: {e}")
        return {}


def create_metadata_template(output_file='video_metadata_template.json'):
    """Tạo template file metadata"""
    template = {
        "example_video.mp4": {
            "title": "Tiêu đề video của bạn",
            "description": "Mô tả chi tiết video\n\nHashtags: #Video #YouTube",
            "tags": ["tag1", "tag2", "tag3"],
            "privacy": "public",
            "category_id": "22"
        },
        "another_video.mp4": {
            "title": "Video khác",
            "description": "Mô tả khác",
            "tags": ["entertainment", "funny"],
            "privacy": "unlisted",
            "category_id": "23"
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Đã tạo template metadata: {output_file}")
    print("📝 Chỉnh sửa file này với thông tin video của bạn, sau đó dùng --metadata")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Direct YouTube Upload - Upload video trực tiếp lên YouTube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  
  # Upload 1 video đơn giản
  python direct_upload.py video.mp4
  
  # Upload với custom title và tags
  python direct_upload.py video.mp4 --title "Video của tôi" --tags "gaming,funny,vietnam"
  
  # Upload private
  python direct_upload.py video.mp4 --privacy private
  
  # Upload với thumbnail
  python direct_upload.py video.mp4 --thumbnail thumb.jpg
  
  # Upload toàn bộ folder
  python direct_upload.py --folder input/ --privacy unlisted
  
  # Upload với metadata file
  python direct_upload.py --folder input/ --metadata video_info.json
  
  # Tạo template metadata
  python direct_upload.py --create-template
        """
    )
    
    parser.add_argument(
        'video_path', 
        nargs='?',
        help='Đường dẫn video cần upload'
    )
    
    parser.add_argument(
        '--folder', 
        help='Upload tất cả video trong folder'
    )
    
    parser.add_argument(
        '--title', 
        help='Tiêu đề video'
    )
    
    parser.add_argument(
        '--description', 
        help='Mô tả video'
    )
    
    parser.add_argument(
        '--tags', 
        help='Tags (ngăn cách bởi dấu phẩy): gaming,funny,vietnam'
    )
    
    parser.add_argument(
        '--privacy', 
        choices=['public', 'private', 'unlisted'],
        default='public',
        help='Privacy setting (default: public)'
    )
    
    parser.add_argument(
        '--thumbnail', 
        help='Đường dẫn thumbnail image'
    )
    
    parser.add_argument(
        '--category', 
        default='22',
        help='YouTube category ID (default: 22 = People & Blogs)'
    )
    
    parser.add_argument(
        '--metadata', 
        help='File JSON chứa metadata cho video'
    )
    
    parser.add_argument(
        '--filter-ext', 
        help='Filter video extensions (ngăn cách bởi phẩy): mp4,avi,mov'
    )
    
    parser.add_argument(
        '--create-template', 
        action='store_true',
        help='Tạo template file metadata'
    )
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Tạo template nếu được yêu cầu
    if args.create_template:
        create_metadata_template()
        return
    
    # Parse tags
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]
    
    # Parse filter extensions
    filter_ext = None
    if args.filter_ext:
        filter_ext = [f".{ext.strip().lower()}" for ext in args.filter_ext.split(',')]
    
    # Load metadata if provided
    metadata = {}
    if args.metadata:
        metadata = load_metadata_from_file(args.metadata)
    
    # Upload folder
    if args.folder:
        if metadata:
            # Upload với metadata
            print("📋 Sử dụng metadata từ file...")
            results = []
            for filename, meta in metadata.items():
                video_path = os.path.join(args.folder, filename)
                if os.path.exists(video_path):
                    print(f"\n📤 Upload: {filename}")
                    result = direct_upload_video(
                        video_path=video_path,
                        title=meta.get('title'),
                        description=meta.get('description'),
                        tags=meta.get('tags', []),
                        privacy=meta.get('privacy', args.privacy),
                        category_id=meta.get('category_id', args.category)
                    )
                    results.append({'file': filename, 'result': result})
                    
                    # Delay
                    import time
                    time.sleep(15)
                else:
                    print(f"⚠️  File không tồn tại: {video_path}")
        else:
            # Upload folder bình thường
            results = upload_from_folder(args.folder, args.privacy, filter_ext)
        return
    
    # Upload single video
    if not args.video_path:
        print("❌ Vui lòng cung cấp video path hoặc --folder")
        parser.print_help()
        sys.exit(1)
    
    result = direct_upload_video(
        video_path=args.video_path,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy=args.privacy,
        thumbnail=args.thumbnail,
        category_id=args.category
    )
    
    # Exit code based on result
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == "__main__":
    main()