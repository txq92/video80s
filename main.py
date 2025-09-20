"""
Main program - Xử lý video và upload lên YouTube Shorts
"""
import os
import sys
import json
import argparse
from datetime import datetime

# Import các module đã tạo
from src import VideoProcessor, process_batch_videos, YouTubeUploader, batch_upload_videos, JsonStorageHandler
from config import (
    YOUTUBE_CONFIG, VIDEO_CONFIG, 
    SUPPORTED_FORMATS,
    setup_directories, validate_config
)


def process_single_video(input_video, auto_upload=False, save_to_db=True):
    """
    Xử lý một video đơn lẻ
    
    Args:
        input_video: Đường dẫn video input
        auto_upload: Tự động upload lên YouTube sau khi xử lý
        save_to_db: Lưu thông tin vào MongoDB
    """
    print("=" * 50)
    print(f"BẮT ĐẦU XỬ LÝ VIDEO: {input_video}")
    print("=" * 50)
    
    # Tạo tên file output
    base_name = os.path.basename(input_video).split('.')[0]
    output_video = os.path.join(
        VIDEO_CONFIG['output_folder'],
        f"shorts_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )
    
    # Khởi tạo video processor
    processor = VideoProcessor(
        input_video=input_video,
        logo_path=VIDEO_CONFIG['logo_path'],
        banner_path=VIDEO_CONFIG['banner_path'],
        output_path=output_video,
        background_style=VIDEO_CONFIG.get('background_style', 'blur'),
        banner_intro_path=VIDEO_CONFIG['banner_intro_path'],
        banner_outro_path=VIDEO_CONFIG['banner_outro_path']
    )
    
    # Xử lý video
    process_result = processor.process_video()
    
    if process_result['status'] == 'success':
        print(f"\n✓ Video đã được xử lý thành công!")
        print(f"  Output: {output_video}")
        print(f"  Duration: {process_result['final_duration']:.2f} giây")
        
        # Chuẩn bị data cho MongoDB
        video_data = {
            **process_result,
            'metadata': {
                'base_name': base_name,
                'process_time': datetime.now().isoformat(),
                'input_filename': os.path.basename(input_video)
            }
        }
        
        # Lưu vào JSON database nếu được yêu cầu
        video_id = None
        if save_to_db:
            try:
                storage_handler = JsonStorageHandler()
                video_id = storage_handler.save_video_info(video_data)
                print(f"\n✓ Đã lưu thông tin vào database")
                print(f"  Video ID: {video_id}")
                print(f"  Video: {os.path.basename(input_video)}")
                storage_handler.close_connection()
            except Exception as e:
                print(f"\n✗ Lỗi khi lưu vào database: {e}")
        
        # Auto upload lên YouTube nếu được yêu cầu
        if auto_upload:
            print("\n" + "=" * 50)
            print("BẮT ĐẦU UPLOAD LÊN YOUTUBE SHORTS")
            print("=" * 50)
            
            try:
                uploader = YouTubeUploader(
                    client_secrets_file=YOUTUBE_CONFIG['client_secrets_file'],
                    credentials_file=YOUTUBE_CONFIG['credentials_file']
                )
                
                # Chuẩn bị metadata cho YouTube
                title = f"{base_name} - {datetime.now().strftime('%d/%m/%Y')}"
                description = f"Video Shorts được tạo tự động\\n\\n#Shorts"
                tags = YOUTUBE_CONFIG['default_tags'] + [base_name]
                
                # Upload video
                upload_result = uploader.upload_video(
                    video_path=output_video,
                    title=title,
                    description=description,
                    tags=tags,
                    privacy_status=YOUTUBE_CONFIG['default_privacy']
                )
                
                if upload_result['status'] == 'success':
                    print(f"\n✓ Upload YouTube thành công!")
                    print(f"  Video ID: {upload_result['video_id']}")
                    print(f"  Shorts URL: {upload_result['shorts_url']}")
                    
                    # Cập nhật database với thông tin YouTube
                    if video_id and save_to_db:
                        try:
                            storage_handler = JsonStorageHandler()
                            storage_handler.update_youtube_info(video_id, upload_result)
                            storage_handler.close_connection()
                        except Exception as e:
                            print(f"Lỗi khi cập nhật YouTube info: {e}")
                else:
                    print(f"\n✗ Upload YouTube thất bại: {upload_result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"\n✗ Lỗi khi upload YouTube: {e}")
        
        return process_result
    else:
        print(f"\n✗ Xử lý video thất bại: {process_result.get('error_message', 'Unknown error')}")
        return process_result


def process_folder(input_folder, auto_upload=False, save_to_db=True):
    """
    Xử lý tất cả video trong một folder
    
    Args:
        input_folder: Folder chứa video
        auto_upload: Tự động upload lên YouTube sau khi xử lý
        save_to_db: Lưu thông tin vào MongoDB
    """
    print("=" * 50)
    print(f"XỬ LÝ FOLDER: {input_folder}")
    print("=" * 50)
    
    # Tìm tất cả video trong folder
    video_files = []
    for file in os.listdir(input_folder):
        if any(file.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
            video_files.append(os.path.join(input_folder, file))
    
    if not video_files:
        print("Không tìm thấy video nào trong folder!")
        return
    
    print(f"Tìm thấy {len(video_files)} video")
    
    results = []
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Xử lý: {os.path.basename(video_file)}")
        result = process_single_video(video_file, auto_upload, save_to_db)
        results.append(result)
    
    # Tổng kết
    success_count = sum(1 for r in results if r['status'] == 'success')
    print("\n" + "=" * 50)
    print(f"HOÀN THÀNH XỬ LÝ")
    print(f"Thành công: {success_count}/{len(results)}")
    print("=" * 50)
    
    return results


def show_statistics():
    """Hiển thị thống kê từ database"""
    try:
        storage_handler = JsonStorageHandler()
        
        stats = storage_handler.get_statistics()
        recent_videos = storage_handler.get_all_videos(limit=5)
        
        print("\n" + "=" * 50)
        print("THỐNG KÊ DATABASE")
        print("=" * 50)
        print(f"Tổng số video: {stats.get('total_videos', 0)}")
        print(f"Xử lý thành công: {stats.get('successful_processing', 0)}")
        print(f"Xử lý thất bại: {stats.get('failed_processing', 0)}")
        print(f"Đã upload YouTube: {stats.get('youtube_uploaded', 0)}")
        print(f"Chờ upload: {stats.get('youtube_pending', 0)}")
        print(f"Lần cập nhật cuối: {stats.get('last_updated', 'N/A')}")
        
        if recent_videos:
            print("\n5 VIDEO GẦN NHẤT:")
            for video in recent_videos:
                input_name = os.path.basename(video.get('input_video', 'Unknown'))
                print(f"- {input_name}")
                print(f"  Status: {video.get('processing_status', 'N/A')}")
                print(f"  Duration: {video.get('final_duration', 'N/A')} seconds")
                if video.get('youtube_info', {}).get('status') == 'success':
                    print(f"  YouTube: {video['youtube_info'].get('shorts_url', 'N/A')}")
                print()
        
        # Export CSV option
        print("\nTùy chọn: Sử dụng --export để xuất dữ liệu ra CSV")
        
        storage_handler.close_connection()
        
    except Exception as e:
        print(f"Lỗi khi lấy thống kê: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Video Processor & YouTube Shorts Uploader'
    )
    
    parser.add_argument(
        'input',
        help='Video file hoặc folder chứa video'
    )
    
    parser.add_argument(
        '--upload',
        action='store_true',
        help='Tự động upload lên YouTube sau khi xử lý'
    )
    
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Không lưu vào database'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Hiển thị thống kê từ database'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export dữ liệu ra file CSV'
    )
    
    parser.add_argument(
        '--direct-upload',
        action='store_true',
        help='Upload trực tiếp lên YouTube không cần edit video'
    )
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Validate configuration
    errors = validate_config()
    if errors and not args.stats and not args.export:
        print("LỖI CẤU HÌNH:")
        for error in errors:
            print(f"  - {error}")
        print("\nVui lòng kiểm tra lại cấu hình và thử lại.")
        sys.exit(1)
    
    # Export to CSV if requested
    if args.export:
        storage_handler = JsonStorageHandler()
        if storage_handler.export_to_csv():
            print("✓ Export thành công!")
        storage_handler.close_connection()
        return
    
    # Show statistics if requested
    if args.stats:
        show_statistics()
        return
    
    # Direct upload mode
    if args.direct_upload:
        from direct_upload import direct_upload_video
        
        if os.path.isfile(args.input):
            print("📤 DIRECT UPLOAD MODE - Không cần edit video")
            result = direct_upload_video(args.input)
            sys.exit(0 if result['status'] == 'success' else 1)
        else:
            print("❌ Direct upload chỉ hỗ trợ single file")
            sys.exit(1)
    
    # Process video(s) - Edit mode
    save_to_db = not args.no_db
    
    if os.path.isfile(args.input):
        # Xử lý file đơn
        process_single_video(args.input, args.upload, save_to_db)
    elif os.path.isdir(args.input):
        # Xử lý folder
        process_folder(args.input, args.upload, save_to_db)
    else:
        print(f"Lỗi: Không tìm thấy '{args.input}'")
        sys.exit(1)


if __name__ == "__main__":
    main()