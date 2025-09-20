"""
Module xử lý lưu trữ thông tin vào JSON file
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid
from threading import Lock


class JsonStorageHandler:
    def __init__(self, storage_file='data/videos_database.json'):
        """
        Khởi tạo JSON Storage Handler
        
        Args:
            storage_file: Đường dẫn đến file JSON lưu trữ dữ liệu
        """
        self.storage_file = storage_file
        self.data_dir = os.path.dirname(storage_file) if os.path.dirname(storage_file) else 'data'
        self.lock = Lock()  # Thread-safe operations
        
        # Tạo thư mục data nếu chưa tồn tại
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Load dữ liệu hiện tại hoặc tạo mới
        self.data = self._load_data()
        print(f"Đã khởi tạo JSON storage: {self.storage_file}")
    
    def _load_data(self) -> Dict:
        """
        Load dữ liệu từ file JSON
        """
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Đã load {len(data.get('videos', []))} videos từ database")
                    return data
            except Exception as e:
                print(f"Lỗi khi load data: {e}")
                return self._create_empty_database()
        else:
            return self._create_empty_database()
    
    def _create_empty_database(self) -> Dict:
        """
        Tạo database rỗng
        """
        return {
            'videos': [],
            'statistics': {
                'total_processed': 0,
                'total_uploaded': 0,
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _save_data(self) -> bool:
        """
        Lưu dữ liệu vào file JSON
        """
        try:
            with self.lock:
                # Backup file cũ nếu tồn tại
                if os.path.exists(self.storage_file):
                    backup_file = f"{self.storage_file}.backup"
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(self.storage_file, backup_file)
                
                # Cập nhật thời gian
                self.data['statistics']['last_updated'] = datetime.now().isoformat()
                
                # Lưu file mới
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
                
                return True
        except Exception as e:
            print(f"Lỗi khi lưu data: {e}")
            # Restore backup nếu có lỗi
            backup_file = f"{self.storage_file}.backup"
            if os.path.exists(backup_file):
                os.rename(backup_file, self.storage_file)
            return False
    
    def save_video_info(self, video_data: Dict) -> Optional[str]:
        """
        Lưu thông tin video vào JSON
        
        Args:
            video_data: Dict chứa thông tin video
        
        Returns:
            ID của video đã được lưu
        """
        try:
            # Tạo ID unique cho video
            video_id = str(uuid.uuid4())
            
            # Format dữ liệu video
            document = {
                'id': video_id,
                'input_video': video_data.get('input_video'),
                'output_video': video_data.get('output_video'),
                'original_duration': video_data.get('original_duration'),
                'final_duration': video_data.get('final_duration'),
                'processing_status': video_data.get('status', 'unknown'),
                'youtube_info': video_data.get('youtube_info', {}),
                'processing_date': datetime.now().isoformat(),
                'metadata': video_data.get('metadata', {})
            }
            
            # Thêm vào danh sách videos
            self.data['videos'].append(document)
            
            # Cập nhật statistics
            self.data['statistics']['total_processed'] += 1
            if document.get('youtube_info', {}).get('status') == 'success':
                self.data['statistics']['total_uploaded'] += 1
            
            # Lưu vào file
            if self._save_data():
                print(f"Đã lưu thông tin video với ID: {video_id}")
                return video_id
            else:
                # Rollback nếu lưu thất bại
                self.data['videos'].pop()
                return None
                
        except Exception as e:
            print(f"Lỗi khi lưu video info: {e}")
            return None
    
    def update_youtube_info(self, video_id: str, youtube_data: Dict) -> bool:
        """
        Cập nhật thông tin YouTube cho video đã xử lý
        
        Args:
            video_id: ID của video
            youtube_data: Dict chứa thông tin YouTube
        """
        try:
            # Tìm video theo ID
            for video in self.data['videos']:
                if video['id'] == video_id:
                    # Cập nhật YouTube info
                    video['youtube_info'] = youtube_data
                    video['updated_at'] = datetime.now().isoformat()
                    
                    # Cập nhật statistics nếu upload thành công
                    if youtube_data.get('status') == 'success':
                        self.data['statistics']['total_uploaded'] += 1
                    
                    # Lưu vào file
                    if self._save_data():
                        print(f"Đã cập nhật YouTube info cho video {video_id}")
                        return True
                    return False
            
            print(f"Không tìm thấy video với ID: {video_id}")
            return False
                
        except Exception as e:
            print(f"Lỗi khi cập nhật YouTube info: {e}")
            return False
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """
        Lấy thông tin video từ database bằng ID
        """
        try:
            for video in self.data['videos']:
                if video['id'] == video_id:
                    return video
            return None
        except Exception as e:
            print(f"Lỗi khi query video: {e}")
            return None
    
    def get_all_videos(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Lấy tất cả video từ database
        
        Args:
            limit: Số lượng video tối đa cần lấy
        """
        try:
            videos = self.data['videos']
            # Sắp xếp theo thời gian xử lý mới nhất
            videos.sort(key=lambda x: x.get('processing_date', ''), reverse=True)
            
            if limit:
                return videos[:limit]
            return videos
        except Exception as e:
            print(f"Lỗi khi query videos: {e}")
            return []
    
    def get_videos_by_status(self, status: str) -> List[Dict]:
        """
        Lấy video theo status xử lý
        """
        try:
            return [v for v in self.data['videos'] if v.get('processing_status') == status]
        except Exception as e:
            print(f"Lỗi khi query videos by status: {e}")
            return []
    
    def get_youtube_uploaded_videos(self) -> List[Dict]:
        """
        Lấy danh sách video đã upload lên YouTube
        """
        try:
            return [v for v in self.data['videos'] 
                   if v.get('youtube_info', {}).get('status') == 'success']
        except Exception as e:
            print(f"Lỗi khi query YouTube videos: {e}")
            return []
    
    def delete_video(self, video_id: str) -> bool:
        """
        Xóa video khỏi database
        """
        try:
            initial_count = len(self.data['videos'])
            self.data['videos'] = [v for v in self.data['videos'] if v['id'] != video_id]
            
            if len(self.data['videos']) < initial_count:
                # Cập nhật statistics
                self.data['statistics']['total_processed'] -= 1
                
                if self._save_data():
                    print(f"Đã xóa video {video_id} khỏi database")
                    return True
            return False
        except Exception as e:
            print(f"Lỗi khi xóa video: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê về videos trong database
        """
        try:
            videos = self.data['videos']
            
            stats = {
                'total_videos': len(videos),
                'successful_processing': len([v for v in videos if v.get('processing_status') == 'success']),
                'failed_processing': len([v for v in videos if v.get('processing_status') == 'error']),
                'youtube_uploaded': len([v for v in videos if v.get('youtube_info', {}).get('status') == 'success']),
                'youtube_pending': 0,
                'last_updated': self.data['statistics'].get('last_updated', 'N/A')
            }
            
            stats['youtube_pending'] = stats['successful_processing'] - stats['youtube_uploaded']
            
            return stats
            
        except Exception as e:
            print(f"Lỗi khi lấy statistics: {e}")
            return {}
    
    def export_to_csv(self, csv_file: str = 'data/videos_export.csv') -> bool:
        """
        Export dữ liệu ra file CSV
        """
        try:
            import csv
            
            if not self.data['videos']:
                print("Không có video nào để export")
                return False
            
            # Chuẩn bị headers
            headers = ['ID', 'Input Video', 'Output Video', 'Duration', 'Status', 
                      'YouTube URL', 'Processing Date']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for video in self.data['videos']:
                    row = [
                        video.get('id', ''),
                        os.path.basename(video.get('input_video', '')),
                        os.path.basename(video.get('output_video', '')),
                        f"{video.get('final_duration', 0):.2f}s",
                        video.get('processing_status', ''),
                        video.get('youtube_info', {}).get('shorts_url', 'N/A'),
                        video.get('processing_date', '')[:10]  # Chỉ lấy ngày
                    ]
                    writer.writerow(row)
            
            print(f"Đã export {len(self.data['videos'])} videos ra file: {csv_file}")
            return True
            
        except Exception as e:
            print(f"Lỗi khi export CSV: {e}")
            return False
    
    def close_connection(self):
        """
        Đóng kết nối (compatibility với code cũ)
        """
        # Lưu lần cuối trước khi đóng
        self._save_data()
        print("Đã lưu và đóng JSON storage")