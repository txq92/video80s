"""
Module xử lý video: resize 9:16, chèn logo, chèn banner
"""
import os
# Apply PIL/Pillow compatibility patch
try:
    from . import pil_patch
except ImportError:
    import pil_patch
try:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
    from moviepy.video.fx import resize as fx_resize
except ImportError:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
    from moviepy.video.fx import resize as fx_resize
from PIL import Image
import numpy as np


class VideoProcessor:
    def __init__(self, input_video, logo_path, banner_path, output_path, background_style='blur'):
        """
        Khởi tạo Video Processor
        
        Args:
            input_video: Đường dẫn video gốc
            logo_path: Đường dẫn file logo
            banner_path: Đường dẫn file banner
            output_path: Đường dẫn xuất video
            background_style: 'blur', 'gradient', 'solid' - kiểu nền cho phần trống
        """
        self.input_video = input_video
        self.logo_path = logo_path
        self.banner_path = banner_path
        self.output_path = output_path
        self.target_aspect_ratio = 9/16  # Tỉ lệ 9:16 cho YouTube Shorts
        self.background_style = background_style
        
    def process_video_bk(self):
        """
        Xử lý video chính
        """
        try:
            print(f"Đang xử lý video: {self.input_video}")
            
            # Load video gốc
            video = VideoFileClip(self.input_video)
            original_duration = video.duration
            
            # Resize video về tỉ lệ 9:16
            # video_resized = self._resize_video_to_portrait(video)
            
            # Chèn logo vào góc phải dưới
            # video_with_logo = self._add_logo(video_resized)
            
            # Chèn banner 20 giây đầu
            # final_video = self._add_banner_intro(video_with_logo)
            
            # Chèn logo vào video gốc (trước khi resize)
            video_with_logo = self._add_logo(video)
            
            # Resize video đã chèn logo về tỉ lệ 9:16
            video_resized = self._resize_video_to_portrait(video_with_logo)
            
            # Chèn banner 20 giây đầu
            final_video = self._add_banner_intro(video_resized)
            
            # Xuất video
            print(f"Đang xuất video đến: {self.output_path}")
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Giải phóng resources
            video.close()
            final_video.close()
            
            print("Hoàn thành xử lý video!")
            return {
                'status': 'success',
                'input_video': self.input_video,
                'output_video': self.output_path,
                'original_duration': original_duration,
                'final_duration': final_video.duration
            }
            
        except Exception as e:
            print(f"Lỗi khi xử lý video: {str(e)}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
    

    def process_video(self):
        try:
            print(f"Đang xử lý video: {self.input_video}")
            
            # Load video gốc
            video = VideoFileClip(self.input_video)
            original_duration = video.duration

            # Giới hạn video nếu dài quá 300s → lấy 280s đầu
            if video.duration > 300:
                video = video.subclip(0, 280)
                print(f"Video dài {original_duration:.1f}s, đã cắt xuống 280s")

            # Chèn logo
            video_with_logo = self._add_logo(video)

            # Resize 9:16
            video_resized = self._resize_video_to_portrait(video_with_logo)

            # Banner 20 giây đầu
            video_with_intro = self._add_banner_intro(video_resized)

            # Banner 5 giây cuối
            final_video = self._add_banner_outro(video_with_intro, duration=5)

            # Xuất file
            print(f"Đang xuất video đến: {self.output_path}")
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )

            # Giải phóng resources
            video.close()
            final_video.close()

            print("Hoàn thành xử lý video!")
            return {
                'status': 'success',
                'input_video': self.input_video,
                'output_video': self.output_path,
                'original_duration': original_duration,
                'final_duration': final_video.duration
            }

        except Exception as e:
            print(f"Lỗi khi xử lý video: {str(e)}")
            return {
                'status': 'error',
                'error_message': str(e)
            }


    def _resize_video_to_portrait(self, video):
        """
        Resize video về tỉ lệ 9:16 (portrait mode) với nền blur
        Giữ toàn bộ nội dung video, thêm nền blur cho phần trống
        """
        from moviepy.video.fx import resize as fx_resize
        from moviepy.video.fx.all import colorx
        import numpy as np
        
        # Kích thước target cho YouTube Shorts
        target_width = 1080
        target_height = 1920
        target_ratio = target_width / target_height  # 9:16
        
        current_ratio = video.w / video.h
        
        # Tạo background theo style
        if self.background_style == 'blur':
            # Tạo nền blur từ video gốc
            background = video.copy()
            
            # Resize background để fill toàn bộ 9:16
            if current_ratio > target_ratio:
                # Video quá rộng - scale theo height
                bg_scale = target_height / video.h
            else:
                # Video quá cao - scale theo width  
                bg_scale = target_width / video.w
                
            background = background.resize(bg_scale * 1.2)  # Scale thêm 20% để blur đẹp hơn
            
            # Crop background về đúng kích thước
            if background.w > target_width:
                x_offset = (background.w - target_width) // 2
                background = background.crop(x1=x_offset, width=target_width, height=target_height)
            if background.h > target_height:
                y_offset = (background.h - target_height) // 2
                background = background.crop(y1=y_offset, width=target_width, height=target_height)
                
            # Làm tối và blur background
            background = background.fx(colorx, 0.3)  # Làm tối 70%
            
            # Thêm Gaussian blur effect bằng cách resize xuống rồi resize lên
            blur_factor = 0.1  # Blur mạnh
            temp_size = (int(background.w * blur_factor), int(background.h * blur_factor))
            background = background.resize(newsize=temp_size)
            background = background.resize(newsize=(target_width, target_height))
            
        elif self.background_style == 'gradient':
            # Tạo gradient background
            from moviepy.video.VideoClip import ColorClip
            # Tạo gradient từ xanh dương đến tím
            top_color = ColorClip(size=(target_width, target_height//2), color=(30, 144, 255))  # Dodger Blue
            bottom_color = ColorClip(size=(target_width, target_height//2), color=(138, 43, 226))  # Blue Violet
            
            # Làm mờ gradient
            top_color = top_color.fx(colorx, 0.8)
            bottom_color = bottom_color.fx(colorx, 0.8)
            
            # Stack gradient
            from moviepy.editor import clips_array
            background = clips_array([[top_color], [bottom_color]])
            background = background.set_duration(video.duration)
            
        else:  # solid color
            # Nền màu đơn giản
            from moviepy.video.VideoClip import ColorClip
            # Màu xanh dương nhạt
            background = ColorClip(size=(target_width, target_height), color=(135, 206, 235))  # Sky Blue
            background = background.set_duration(video.duration)
        
        # Resize video chính để fit trong frame 9:16 mà không bị cắt
        if current_ratio > target_ratio:
            # Video quá rộng - scale theo width
            new_width = target_width
            new_height = int(target_width / current_ratio)
        else:
            # Video quá cao - scale theo height
            new_height = target_height
            new_width = int(target_height * current_ratio)
            
        # Đảm bảo không vượt quá kích thước target
        if new_height > target_height:
            scale_factor = target_height / new_height
            new_height = target_height
            new_width = int(new_width * scale_factor)
        if new_width > target_width:
            scale_factor = target_width / new_width
            new_width = target_width
            new_height = int(new_height * scale_factor)
            
        # Resize video chính
        main_video = video.resize(newsize=(new_width, new_height))
        
        # Tính toán vị trí để center video
        x_pos = (target_width - new_width) // 2
        y_pos = (target_height - new_height) // 2
        
        # Đặt video chính ở giữa
        main_video = main_video.set_position((x_pos, y_pos))
        
        # Composite: background blur + video chính
        final_video = CompositeVideoClip([background, main_video], size=(target_width, target_height))
        
        print(f"Đã resize video từ {video.w}x{video.h} về {target_width}x{target_height} (9:16)")
        print(f"Video chính: {new_width}x{new_height} (giữ nguyên nội dung)")
        print(f"Background style: {self.background_style}")
        
        return final_video
    
    def _add_logo(self, video):
        """
        Thêm logo vào góc phải dưới của video
        """
        if not os.path.exists(self.logo_path):
            print(f"Cảnh báo: Không tìm thấy logo tại {self.logo_path}")
            return video
        
        # Load logo
        logo = ImageClip(self.logo_path, transparent=True)
        
        # Resize logo (chiếm khoảng 15% chiều rộng video)
        logo_width = int(video.w * 0.15)
        logo = logo.resize(width=logo_width)
        
        # Đặt logo ở góc phải dưới với padding
        padding = 15
        logo = logo.set_position((video.w - logo.w - padding, video.h - logo.h - padding))
        
        # Set duration cho logo bằng với video
        logo = logo.set_duration(video.duration)
        
        # Composite logo lên video
        video_with_logo = CompositeVideoClip([video, logo])
        
        print("Đã thêm logo vào video")
        return video_with_logo
    
    def _add_banner_intro(self, video):
        """
        Thêm banner che toàn bộ video trong 20 giây đầu
        """
        if not os.path.exists(self.banner_path):
            print(f"Cảnh báo: Không tìm thấy banner tại {self.banner_path}")
            return video
        
        # Load và resize banner để phù hợp với kích thước video
        banner = ImageClip(self.banner_path)
        banner = banner.resize(newsize=(video.w, video.h))
        banner = banner.set_duration(20)  # Banner hiển thị trong 20 giây
        
        # Tạo video với banner 20 giây đầu
        if video.duration <= 20:
            # Nếu video ngắn hơn 20 giây, chỉ hiển thị banner
            final_video = banner.set_duration(video.duration)
            # Giữ audio từ video gốc
            final_video = final_video.set_audio(video.audio)
        else:
            # Lấy phần video sau 20 giây
            video_after_banner = video.subclip(20)
            
            # Lấy audio từ toàn bộ video gốc
            audio_full = video.audio
            
            # Ghép banner với phần video còn lại
            final_video = concatenate_videoclips([banner, video_after_banner])
            
            # Set lại audio cho toàn bộ video
            final_video = final_video.set_audio(audio_full)
        
        print("Đã thêm banner intro 20 giây")
        return final_video

    def _add_banner_outro(self, video, duration=5):
        """
        Thêm banner che toàn bộ video trong N giây cuối (default = 5 giây)
        """
        if not os.path.exists(self.banner_path):
            print(f"Cảnh báo: Không tìm thấy banner tại {self.banner_path}")
            return video

        if video.duration <= duration:
            # Nếu video quá ngắn thì chỉ chèn banner toàn bộ
            banner = ImageClip(self.banner_path).resize(newsize=(video.w, video.h))
            banner = banner.set_duration(video.duration)
            banner = banner.set_audio(video.audio)
            print(f"Đã thêm banner outro {duration} giây (video ngắn)")
            return banner

        # Load banner và resize bằng kích thước video
        banner = ImageClip(self.banner_path).resize(newsize=(video.w, video.h))
        banner = banner.set_duration(duration)

        # Cắt video thành 2 phần
        video_before = video.subclip(0, video.duration - duration)
        video_outro = video.subclip(video.duration - duration, video.duration)

        # Lấy audio đầy đủ từ video gốc
        audio_full = video.audio

        # Ghép: phần trước + banner outro
        final_video = concatenate_videoclips([video_before, banner])

        # Gắn lại audio đầy đủ
        final_video = final_video.set_audio(audio_full)

        print(f"Đã thêm banner outro {duration} giây")
        return final_video

    def _create_thumbnail(self):
        """
        Tạo thumbnail từ video (optional)
        """
        video = VideoFileClip(self.output_path)
        # Lấy frame ở giây thứ 5
        frame = video.get_frame(5)
        thumbnail_path = self.output_path.replace('.mp4', '_thumbnail.jpg')
        
        # Save thumbnail
        from PIL import Image
        img = Image.fromarray(frame)
        img.save(thumbnail_path)
        
        video.close()
        return thumbnail_path


def process_batch_videos(video_folder, logo_path, banner_path, output_folder):
    """
    Xử lý nhiều video trong một folder
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    results = []
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    for filename in os.listdir(video_folder):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            input_path = os.path.join(video_folder, filename)
            output_filename = f"processed_{filename.split('.')[0]}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            processor = VideoProcessor(input_path, logo_path, banner_path, output_path)
            result = processor.process_video()
            results.append(result)
    
    return results