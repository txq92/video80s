#!/usr/bin/env python3
"""
Debug script để test auto-upload functionality
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.youtube_uploader import YouTubeUploader
from config import VIDEO_CONFIG, YOUTUBE_CONFIG, setup_directories

def test_youtube_credentials():
    """Test YouTube credentials"""
    print("🔐 Testing YouTube credentials...")
    
    # Check files exist
    client_secrets = YOUTUBE_CONFIG['client_secrets_file']
    credentials_file = YOUTUBE_CONFIG['credentials_file']
    
    print(f"📁 Client secrets: {client_secrets}")
    print(f"   Exists: {os.path.exists(client_secrets)}")
    
    print(f"📁 Credentials file: {credentials_file}")
    print(f"   Exists: {os.path.exists(credentials_file)}")
    
    if not os.path.exists(client_secrets):
        print("❌ client_secrets.json không tồn tại!")
        return False
    
    # Test authentication
    try:
        uploader = YouTubeUploader(
            client_secrets_file=client_secrets,
            credentials_file=credentials_file
        )
        
        if uploader.youtube:
            print("✅ YouTube authentication thành công!")
            
            # Get channel info
            channels = uploader.get_my_channels()
            if channels:
                for channel in channels:
                    print(f"📺 Channel: {channel['channel_title']} (ID: {channel['channel_id']})")
            
            return True
        else:
            print("❌ YouTube authentication thất bại!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi authentication: {e}")
        return False

def test_upload_function():
    """Test upload function trực tiếp"""
    print("\n🧪 Testing upload function...")
    
    # Tạo một video test nhỏ (giả lập)
    test_video_path = "output/test_video_for_upload.txt"
    
    # Tạo fake video file để test (thực tế cần video thật)
    os.makedirs("output", exist_ok=True)
    with open(test_video_path, 'w') as f:
        f.write("This is a test file, not a real video")
    
    print(f"📁 Test file: {test_video_path}")
    
    try:
        from app import upload_processed_video_to_youtube
        
        # Test function
        result = upload_processed_video_to_youtube("test-job-id", test_video_path)
        
        print(f"📊 Result: {result}")
        
        if result['status'] == 'error':
            print(f"❌ Upload function failed: {result['message']}")
            return False
        else:
            print("✅ Upload function completed")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi test upload function: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_video_path):
            os.remove(test_video_path)

def check_form_data_processing():
    """Check if form data is processed correctly"""
    print("\n📝 Checking form data processing...")
    
    # Simulate checkbox values
    test_cases = [
        ('on', True),      # HTML checkbox checked
        ('true', True),    # Explicit true
        ('false', False),  # Explicit false
        ('', False),       # Empty string
        (None, False)      # None value
    ]
    
    for form_value, expected in test_cases:
        if form_value is None:
            auto_upload_value = 'false'  # Default value
        else:
            auto_upload_value = str(form_value).lower()
        
        # Use the same logic as app.py
        auto_upload = auto_upload_value in ['true', 'on', '1']
        
        result = auto_upload
        status = "✅" if result == expected else "❌"
        print(f"{status} '{form_value}' -> {result} (expected: {expected})")
    
    # Test the actual logic from app.py
    print("\n🔧 Testing actual form processing logic:")
    
    class MockRequest:
        def __init__(self, form_data):
            self.form = form_data
        
        def get(self, key, default):
            return self.form.get(key, default)
    
    test_forms = [
        {'auto_upload': 'on'},      # Checkbox checked
        {'auto_upload': 'true'},    # Explicit true
        {'auto_upload': 'false'},   # Explicit false
        {},                         # No checkbox (unchecked)
    ]
    
    for i, form_data in enumerate(test_forms):
        mock_form = MockRequest(form_data)
        auto_upload_value = mock_form.get('auto_upload', 'false').lower()
        auto_upload = auto_upload_value in ['true', 'on', '1']
        print(f"Test {i+1}: {form_data} -> auto_upload = {auto_upload}")

def main():
    """Main function"""
    print("=" * 60)
    print("🎬 Video80s - Auto Upload Debug")
    print("=" * 60)
    
    setup_directories()
    
    # Test 1: Credentials
    creds_ok = test_youtube_credentials()
    
    # Test 2: Upload function (if credentials OK)
    if creds_ok:
        upload_ok = test_upload_function()
    else:
        upload_ok = False
        print("⏭️ Skipping upload test due to credential issues")
    
    # Test 3: Form data processing
    check_form_data_processing()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print(f"✅ Credentials: {'OK' if creds_ok else 'FAILED'}")
    print(f"✅ Upload Function: {'OK' if upload_ok else 'FAILED'}")
    print("✅ Form Processing: Check output above")
    
    if creds_ok and upload_ok:
        print("\n🎉 Auto-upload should work!")
        print("💡 If it still doesn't work, check:")
        print("   1. JavaScript is sending auto_upload=on when checked")
        print("   2. Server logs for any errors during processing")
        print("   3. Job status API returns show the upload attempt")
    else:
        print("\n❌ Auto-upload has issues that need fixing")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()