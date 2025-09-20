"""
Configuration file cho project
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DATA_CONFIG = {
    'storage_file': os.getenv('DATABASE_FILE', 'data/videos_database.json'),
    'backup_enabled': os.getenv('BACKUP_ENABLED', 'true').lower() == 'true',
    'csv_export_path': os.getenv('CSV_EXPORT_PATH', 'data/videos_export.csv')
}

# YouTube Configuration
YOUTUBE_CONFIG = {
    'client_secrets_file': 'client_secrets.json',
    'credentials_file': 'token.pickle',
    'default_privacy': 'public',  # public, private, unlisted
    'category_id': '22',  # 22 = People & Blogs
    'default_tags': ['Shorts', 'YouTube Shorts', 'Video']
}

# Video Processing Configuration
VIDEO_CONFIG = {
    'logo_path': os.getenv('DEFAULT_LOGO_PATH', 'assets/logo.png'),
    'banner_path': os.getenv('DEFAULT_BANNER_PATH', 'assets/banner.png'),
    'input_folder': os.getenv('INPUT_FOLDER', 'input'),
    'output_folder': os.getenv('OUTPUT_FOLDER', 'output'),
    'temp_folder': 'temp',
    'banner_duration': 20,  # seconds
    'target_resolution': (1080, 1920),  # 9:16 aspect ratio for Shorts
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'background_style': os.getenv('BACKGROUND_STYLE', 'blur'),  # blur, gradient, solid
    'banner_intro_path': os.getenv('DEFAULT_INTRO_PATH', 'assets/intro.png'),
    'banner_outro_path': os.getenv('DEFAULT_OUTRO_PATH', 'assets/outro.png'),
}

# Supported video formats
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']

# Create necessary directories
def setup_directories():
    """Tạo các thư mục cần thiết nếu chưa tồn tại"""
    directories = [
        VIDEO_CONFIG['input_folder'],
        VIDEO_CONFIG['output_folder'],
        VIDEO_CONFIG['temp_folder'],
        'assets',
        'data',
        'logs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Đã tạo thư mục: {directory}")

# Validate configuration
def validate_config():
    """Kiểm tra cấu hình"""
    errors = []
    
    # Check for YouTube client secrets
    if not os.path.exists(YOUTUBE_CONFIG['client_secrets_file']):
        errors.append(f"Không tìm thấy file {YOUTUBE_CONFIG['client_secrets_file']}. Vui lòng tạo OAuth 2.0 credentials từ Google Cloud Console.")
    
    # Check for assets
    if not os.path.exists(VIDEO_CONFIG['logo_path']):
        errors.append(f"Không tìm thấy logo tại {VIDEO_CONFIG['logo_path']}")
    
    if not os.path.exists(VIDEO_CONFIG['banner_path']):
        errors.append(f"Không tìm thấy banner tại {VIDEO_CONFIG['banner_path']}")
    
    return errors