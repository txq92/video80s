#!/usr/bin/env python3
"""
Test script để kiểm tra tính năng upload custom intro/outro banners
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.video_processor import VideoProcessor
from config import VIDEO_CONFIG, setup_directories

def test_with_custom_banners():
    """Test video processing với custom banners"""
    print("🧪 Testing with custom intro/outro banners...")
    
    # Setup directories
    setup_directories()
    
    # Giả sử có video test và custom banners
    test_video = "input/test_video.mp4"
    custom_intro = "temp/custom_intro.png" 
    custom_outro = "temp/custom_outro.png"
    output_path = "output/test_custom_banners.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Test video không tồn tại: {test_video}")
        print("💡 Cần có video test trong thư mục input/")
        return False
    
    # Test 1: Với custom intro/outro
    print("\n📝 Test 1: Với custom intro và outro")
    try:
        processor = VideoProcessor(
            input_video=test_video,
            logo_path=VIDEO_CONFIG['logo_path'],
            banner_path=VIDEO_CONFIG['banner_path'],
            output_path=output_path,
            background_style="blur",
            banner_intro_path=custom_intro if os.path.exists(custom_intro) else None,
            banner_outro_path=custom_outro if os.path.exists(custom_outro) else None
        )
        
        result = processor.process_video()
        if result['status'] == 'success':
            print("✅ Test 1 thành công!")
        else:
            print(f"❌ Test 1 thất bại: {result.get('error_message')}")
            
    except Exception as e:
        print(f"❌ Test 1 lỗi: {e}")
    
    # Test 2: Không có custom banners
    print("\n📝 Test 2: Không có custom banners")
    output_path2 = "output/test_no_custom_banners.mp4"
    
    try:
        processor2 = VideoProcessor(
            input_video=test_video,
            logo_path=VIDEO_CONFIG['logo_path'],
            banner_path=VIDEO_CONFIG['banner_path'],
            output_path=output_path2,
            background_style="blur",
            banner_intro_path=None,  # Không có custom intro
            banner_outro_path=None   # Không có custom outro
        )
        
        result2 = processor2.process_video()
        if result2['status'] == 'success':
            print("✅ Test 2 thành công!")
        else:
            print(f"❌ Test 2 thất bại: {result2.get('error_message')}")
            
    except Exception as e:
        print(f"❌ Test 2 lỗi: {e}")
    
    return True

def create_sample_banners():
    """Tạo sample banner images để test"""
    print("🎨 Tạo sample banner images...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Tạo intro banner
        intro_img = Image.new('RGB', (1080, 1920), color='#1E3A8A')  # Blue
        draw = ImageDraw.Draw(intro_img)
        
        # Thêm text
        try:
            # Try to use a default font, fallback to default if not available
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        draw.text((540, 960), "CUSTOM INTRO", font=font, fill='white', anchor='mm')
        intro_path = "temp/custom_intro.png"
        intro_img.save(intro_path)
        print(f"✅ Tạo intro banner: {intro_path}")
        
        # Tạo outro banner
        outro_img = Image.new('RGB', (1080, 1920), color='#DC2626')  # Red
        draw2 = ImageDraw.Draw(outro_img)
        draw2.text((540, 960), "CUSTOM OUTRO", font=font, fill='white', anchor='mm')
        outro_path = "temp/custom_outro.png"
        outro_img.save(outro_path)
        print(f"✅ Tạo outro banner: {outro_path}")
        
        return True
        
    except ImportError:
        print("❌ Pillow không có sẵn. Chạy: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ Lỗi tạo sample banners: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🎬 Video80s - Custom Banner Test")
    print("=" * 60)
    
    # Tạo sample banners nếu cần
    if not os.path.exists("temp/custom_intro.png") or not os.path.exists("temp/custom_outro.png"):
        if not create_sample_banners():
            print("Sẽ test mà không có custom banners")
    
    # Test functionality
    success = test_with_custom_banners()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test hoàn tất!")
        print("💡 Kiểm tra video output trong thư mục output/")
        print("🌐 Test trên web interface: http://localhost:5000/upload")
    else:
        print("❌ Test chưa hoàn tất. Kiểm tra lại setup.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")