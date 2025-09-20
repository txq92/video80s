#!/usr/bin/env python3
"""
Script kiểm tra tính hợp lệ của client_secrets.json
"""
import os
import json
import sys


def check_client_secrets():
    """Kiểm tra file client_secrets.json"""
    print("🔍 KIỂM TRA GOOGLE OAUTH CREDENTIALS")
    print("=" * 50)
    
    # Kiểm tra file tồn tại
    if not os.path.exists('client_secrets.json'):
        print("❌ File client_secrets.json không tồn tại!")
        print("💡 Cần tạo file này từ Google Cloud Console")
        return False
    
    # Đọc và parse JSON
    try:
        with open('client_secrets.json', 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ File client_secrets.json không hợp lệ: {e}")
        return False
    
    # Kiểm tra cấu trúc
    if 'installed' not in data:
        print("❌ File thiếu section 'installed'")
        return False
    
    installed = data['installed']
    required_fields = ['client_id', 'client_secret', 'project_id']
    
    print("📋 Kiểm tra các trường bắt buộc:")
    
    for field in required_fields:
        if field not in installed:
            print(f"❌ Thiếu trường '{field}'")
            return False
        
        value = installed[field]
        
        # Kiểm tra placeholder values
        if field == 'client_id':
            if value.startswith('YOUR_CLIENT_ID') or 'your-client-id' in value.lower():
                print(f"❌ {field}: Vẫn là placeholder - {value}")
                print("   👉 Cần thay bằng client_id thật từ Google Console")
                return False
            elif not value.endswith('.apps.googleusercontent.com'):
                print(f"❌ {field}: Format không đúng - {value}")
                print("   👉 Client ID phải có format: xxxxx.apps.googleusercontent.com")
                return False
            else:
                print(f"✅ {field}: OK")
                
        elif field == 'client_secret':
            if value.startswith('YOUR_CLIENT_SECRET') or 'your-client-secret' in value.lower():
                print(f"❌ {field}: Vẫn là placeholder")
                print("   👉 Cần thay bằng client_secret thật từ Google Console")
                return False
            elif not value.startswith('GOCSPX-'):
                print(f"❌ {field}: Format không đúng")
                print("   👉 Client secret thường bắt đầu bằng 'GOCSPX-'")
                return False
            else:
                print(f"✅ {field}: OK")
                
        elif field == 'project_id':
            if 'your-project' in value.lower():
                print(f"❌ {field}: Vẫn là placeholder - {value}")
                print("   👉 Cần thay bằng project_id thật từ Google Console")
                return False
            else:
                print(f"✅ {field}: OK - {value}")
    
    # Kiểm tra redirect URIs
    if 'redirect_uris' in installed:
        redirect_uris = installed['redirect_uris']
        if 'http://localhost' not in redirect_uris and 'urn:ietf:wg:oauth:2.0:oob' not in redirect_uris:
            print("⚠️  redirect_uris: Nên chứa 'http://localhost' hoặc 'urn:ietf:wg:oauth:2.0:oob'")
        else:
            print("✅ redirect_uris: OK")
    
    print("\n✅ File client_secrets.json hợp lệ!")
    print("🎯 Có thể chạy upload script")
    return True


def check_youtube_api_enabled():
    """Hướng dẫn kiểm tra YouTube API"""
    print("\n" + "=" * 50)
    print("📺 KIỂM TRA YOUTUBE DATA API V3")
    print("=" * 50)
    print("Để kiểm tra YouTube API đã enable chưa:")
    print("1. Truy cập: https://console.cloud.google.com/")
    print("2. Chọn project của bạn")
    print("3. Vào APIs & Services → Library")
    print("4. Tìm 'YouTube Data API v3'")
    print("5. Đảm bảo trạng thái là 'ENABLED'")
    print("\nNếu chưa enable, click 'ENABLE' button")


def main():
    """Main function"""
    print("🔧 GOOGLE OAUTH SETUP CHECKER")
    print("=" * 50)
    
    is_valid = check_client_secrets()
    
    if not is_valid:
        print("\n❌ SETUP CHƯA ĐÚNG!")
        print("📖 Vui lòng đọc file SETUP_GOOGLE_OAUTH.md để biết cách setup")
        print("🌐 Hoặc truy cập: https://console.cloud.google.com/")
        sys.exit(1)
    else:
        check_youtube_api_enabled()
        print("\n🎉 SETUP HOÀN TẤT!")
        print("💡 Bây giờ có thể chạy upload scripts:")
        print("   python quick_upload.py video.mp4")
        print("   python direct_upload.py video.mp4")
        sys.exit(0)


if __name__ == "__main__":
    main()