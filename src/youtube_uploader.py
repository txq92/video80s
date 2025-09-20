"""
Module upload video lên YouTube Shorts - Hỗ trợ cả Windows và Linux
"""
import os
import random
import time
import sys
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle
import json


class YouTubeUploader:
    def __init__(self, client_secrets_file='client_secrets.json', credentials_file='token.pickle'):
        """
        Khởi tạo YouTube Uploader
        
        Args:
            client_secrets_file: File chứa client secrets từ Google Console
            credentials_file: File lưu credentials đã xác thực
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_file = credentials_file
        self.youtube = None
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        # Các category ID phổ biến trên YouTube
        self.VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')
        
        # Authenticate và build service
        self._authenticate()
    
    def _authenticate(self):
        """
        Xác thực với YouTube API - Hỗ trợ cả Windows và Linux
        """
        creds = None
        
        # Load credentials đã lưu nếu có
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'rb') as token:
                    creds = pickle.load(token)
                print(f"Đã load credentials từ {self.credentials_file}")
            except Exception as e:
                print(f"Lỗi khi load credentials: {e}")
                creds = None
        
        # Nếu không có credentials hoặc đã hết hạn
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("Đang refresh token...")
                    creds.refresh(Request())
                    print("Token đã được refresh thành công")
                except Exception as e:
                    print(f"Không thể refresh token: {e}")
                    creds = None
            
            # Nếu vẫn không có credentials hợp lệ
            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    print(f"Lỗi: Không tìm thấy file {self.client_secrets_file}")
                    print("Vui lòng tạo OAuth 2.0 credentials từ Google Console")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.SCOPES)
                
                # Thử authentication theo môi trường
                creds = self._try_authentication(flow)
                if not creds:
                    print("Xác thực thất bại")
                    return False
            
            # Lưu credentials cho lần sau
            try:
                with open(self.credentials_file, 'wb') as token:
                    pickle.dump(creds, token)
                print(f"Đã lưu credentials vào {self.credentials_file}")
            except Exception as e:
                print(f"Cảnh báo: Không thể lưu credentials: {e}")
        
        # Build YouTube service
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            print("Đã xác thực thành công với YouTube API")
            return True
        except Exception as e:
            print(f"Lỗi khi build YouTube service: {e}")
            return False
    
    def _try_authentication(self, flow):
        """
        Thử các phương thức authentication khác nhau
        """
        # Method 1: Local server (cho desktop)
        try:
            print("Thử authentication qua local server...")
            creds = flow.run_local_server(port=0)
            print("Authentication thành công qua local server")
            return creds
        except Exception as e:
            print(f"Local server authentication thất bại: {e}")
        
        # Method 2: Console (cho server hoặc khi local server fail)
        try:
            print("Chuyển sang console authentication...")
            print("Sao chép URL sau vào browser để xác thực:")
            creds = flow.run_console()
            print("Authentication thành công qua console")
            return creds
        except Exception as e:
            print(f"Console authentication thất bại: {e}")
        
        return None
    
    def upload_video(self, video_path, title, description, tags=None, category_id='22', 
                     privacy_status='public', thumbnail_path=None, notify_subscribers=False):
        """
        Upload video lên YouTube
        
        Args:
            video_path: Đường dẫn đến video file
            title: Tiêu đề video (tối đa 100 ký tự)
            description: Mô tả video
            tags: List các tag cho video
            category_id: ID category (mặc định 22 = People & Blogs)
            privacy_status: 'private', 'public', hoặc 'unlisted'
            thumbnail_path: Đường dẫn đến thumbnail (optional)
            notify_subscribers: Có thông báo cho subscribers không
        
        Returns:
            Dict chứa thông tin video đã upload hoặc error
        """
        if not self.youtube:
            return {'status': 'error', 'message': 'Chưa xác thực với YouTube API'}
        
        if not os.path.exists(video_path):
            return {'status': 'error', 'message': f'Không tìm thấy video: {video_path}'}
        
        # Validate privacy status
        if privacy_status not in self.VALID_PRIVACY_STATUSES:
            privacy_status = 'private'  # Default safe option
        
        # Chuẩn bị metadata cho video
        if tags is None:
            tags = []
        
        # Đảm bảo tags là list và không có duplicate
        tags = list(set(tags)) if isinstance(tags, list) else []
        
        # Thêm hashtag #Shorts để video được nhận diện là YouTube Shorts
        if 'Shorts' not in tags:
            tags.append('Shorts')
        
        # Đảm bảo title không quá dài và clean text
        if len(title) > 100:
            title = title[:97] + '...'
        
        # Clean text để tránh lỗi encoding
        title = self._clean_text(title)
        description = self._clean_text(description)
        
        # Thêm #Shorts vào description nếu chưa có
        if '#Shorts' not in description:
            description = description + '\n\n#Shorts'
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': str(category_id)
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
                'notifySubscribers': notify_subscribers
            }
        }
        
        # Chuẩn bị file upload
        try:
            # Kiểm tra file size
            file_size = os.path.getsize(video_path)
            if file_size > 2 * 1024 * 1024 * 1024:  # 2GB warning
                print(f"Cảnh báo: File size {file_size / (1024*1024*1024):.2f}GB có thể upload chậm")
            
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024,  # 1MB chunks for better progress tracking
                resumable=True,
                mimetype='video/*'
            )
        except Exception as e:
            return {'status': 'error', 'message': f'Lỗi khi chuẩn bị file upload: {str(e)}'}
        
        # Get file size for logging
        file_size = os.path.getsize(video_path)
        
        try:
            # Thực hiện upload
            print(f"Đang upload video: {title}")
            print(f"File: {video_path}")
            print(f"Size: {file_size / (1024*1024):.2f} MB")
            print(f"Privacy: {privacy_status}")
            
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute upload với resumable upload
            response = None
            retry = 0
            max_retries = 5
            
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"Đã upload {progress}%")
                        
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retry với exponential backoff
                        print(f"HTTP {e.resp.status} error, đang thử lại...")
                        retry += 1
                        if retry > max_retries:
                            return {
                                'status': 'error',
                                'message': f'Upload thất bại sau {max_retries} lần thử: HTTP {e.resp.status}'
                            }
                        sleep_time = (2 ** retry) + (random.randint(0, 1000) / 1000)
                        print(f"Đợi {sleep_time:.1f}s trước khi thử lại...")
                        time.sleep(sleep_time)
                    else:
                        return {
                            'status': 'error',
                            'message': f'HTTP Error {e.resp.status}: {e.content.decode("utf-8", errors="ignore")}'
                        }
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'Lỗi không xác định: {str(e)}'
                    }
            
            if response is not None:
                video_id = response.get('id')
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                shorts_url = f"https://youtube.com/shorts/{video_id}"
                
                print(f"Upload thành công!")
                print(f"Video ID: {video_id}")
                print(f"URL: {video_url}")
                print(f"Shorts URL: {shorts_url}")
                
                # Upload thumbnail nếu có
                if thumbnail_path and os.path.exists(thumbnail_path):
                    thumbnail_result = self._upload_thumbnail(video_id, thumbnail_path)
                    if not thumbnail_result:
                        print("Cảnh báo: Upload thumbnail thất bại, nhưng video đã upload thành công")
                
                return {
                    'status': 'success',
                    'video_id': video_id,
                    'video_url': video_url,
                    'shorts_url': shorts_url,
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'privacy_status': privacy_status,
                    'file_size': file_size
                }
            
        except Exception as e:
            error_message = f'Lỗi upload: {str(e)}'
            print(error_message)
            return {
                'status': 'error',
                'message': error_message
            }
    
    def _clean_text(self, text):
        """
        Clean text để tránh lỗi encoding
        """
        if not text:
            return ""
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        return text.strip()
    
    def _upload_thumbnail(self, video_id, thumbnail_path):
        """
        Upload thumbnail cho video
        """
        try:
            # Validate thumbnail file
            if not os.path.exists(thumbnail_path):
                print(f"Thumbnail không tồn tại: {thumbnail_path}")
                return False
            
            # Check file size (thumbnail max 2MB)
            thumb_size = os.path.getsize(thumbnail_path)
            if thumb_size > 2 * 1024 * 1024:
                print(f"Thumbnail quá lớn: {thumb_size / (1024*1024):.2f}MB (max 2MB)")
                return False
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"Đã upload thumbnail cho video {video_id}")
            return True
        except HttpError as e:
            print(f"Lỗi khi upload thumbnail: HTTP {e.resp.status}")
            return False
        except Exception as e:
            print(f"Lỗi khi upload thumbnail: {e}")
            return False
    
    def get_my_channels(self):
        """
        Lấy thông tin các channel của user
        """
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            channels = []
            for item in response.get('items', []):
                channel_info = {
                    'channel_id': item['id'],
                    'channel_title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'subscriber_count': item['statistics'].get('subscriberCount', 'N/A'),
                    'video_count': item['statistics'].get('videoCount', 'N/A'),
                    'view_count': item['statistics'].get('viewCount', 'N/A')
                }
                channels.append(channel_info)
            
            return channels
        except Exception as e:
            print(f"Lỗi khi lấy thông tin channel: {e}")
            return []
    
    def get_video_details(self, video_id):
        """
        Lấy thông tin chi tiết của một video
        """
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,status',
                id=video_id
            ).execute()
            
            if response['items']:
                item = response['items'][0]
                return {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'view_count': item['statistics'].get('viewCount', 0),
                    'like_count': item['statistics'].get('likeCount', 0),
                    'comment_count': item['statistics'].get('commentCount', 0),
                    'privacy_status': item['status']['privacyStatus']
                }
            return None
        except Exception as e:
            print(f"Lỗi khi lấy thông tin video: {e}")
            return None


def batch_upload_videos(video_folder, uploader, metadata_file='video_metadata.json'):
    """
    Upload nhiều video từ một folder
    
    Args:
        video_folder: Folder chứa video
        uploader: Instance của YouTubeUploader
        metadata_file: File JSON chứa metadata cho mỗi video
    """
    # Load metadata nếu có
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    results = []
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    
    for filename in os.listdir(video_folder):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            video_path = os.path.join(video_folder, filename)
            
            # Lấy metadata cho video này hoặc dùng default
            video_meta = metadata.get(filename, {})
            title = video_meta.get('title', f'Video {filename.split(".")[0]}')
            description = video_meta.get('description', 'YouTube Shorts video')
            tags = video_meta.get('tags', ['Shorts'])
            
            # Upload video
            result = uploader.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status='public'
            )
            
            results.append({
                'filename': filename,
                'upload_result': result
            })
            
            # Delay giữa các upload để tránh rate limit
            if result['status'] == 'success':
                print(f"✓ Upload thành công: {filename}")
            else:
                print(f"✗ Upload thất bại: {filename} - {result.get('message', 'Unknown error')}")
            
            time.sleep(10)  # Wait 10 seconds between uploads
    
    return results
