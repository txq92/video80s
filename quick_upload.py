#!/usr/bin/env python3
"""
Quick Upload - Script đơn giản để upload nhanh video lên YouTube
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.youtube_uploader import YouTubeUploader
from config import YOUTUBE_CONFIG, setup_directories


def quick_upload(video_path, title=None):
    """Upload nhanh video lên YouTube với setup tối thiểu"""
    
    if not os.path.exists(video_path):
        print(f"❌ File không tồn tại: {video_path}")
        return False
    
    # Setup directories
    setup_directories()
    
    # Auto title nếu không có
    if not title:
        filename = os.path.basename(video_path)
        title = os.path.splitext(filename)[0]
    
    print(f"🚀 Đang upload: {video_path}")
    print(f"📝 Title: {title}")
    
    try:
        # Tạo uploader
        uploader = YouTubeUploader(
            client_secrets_file=YOUTUBE_CONFIG['client_secrets_file'],
            credentials_file=YOUTUBE_CONFIG['credentials_file']
        )
        
        # Upload video
        result = uploader.upload_video(
            video_path=video_path,
            title=title,
            description=f"Video: {title}\n\nUploaded via Quick Upload\n\n#Video #YouTube",
            tags=['Video', 'Upload'],
            privacy_status='public'
        )
        
        if result['status'] == 'success':
            print("✅ Upload thành công!")
            print(f"🔗 URL: {result['video_url']}")
            print(f"📱 Shorts: {result['shorts_url']}")
            return True
        else:
            print(f"❌ Upload thất bại: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_upload.py <video_file> [title]")
        print("Example: python quick_upload.py video.mp4 \"My Video Title\"")
        sys.exit(1)
    
    video_file = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = quick_upload(video_file, title)
    sys.exit(0 if success else 1)