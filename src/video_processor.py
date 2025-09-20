"""
Module xử lý video: resize 9:16, chèn logo, chèn banner (intro/outro)
"""
import os

# Apply PIL/Pillow compatibility patch (giữ tương thích với các bản Pillow)
try:
    from . import pil_patch
except ImportError:
    import pil_patch  # type: ignore

from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
    clips_array,
)
from moviepy.video.fx.all import colorx  # dùng cho làm tối background
from PIL import Image  # noqa: F401  # (được dùng khi tạo thumbnail)
import numpy as np  # noqa: F401


class VideoProcessor:
    def __init__(
        self,
        input_video: str,
        logo_path: str,
        banner_path: str,              # giữ để tương thích cũ
        output_path: str,
        background_style: str = "blur",
        banner_intro_path: str | None = None,
        banner_outro_path: str | None = None,
    ):
        """
        Args:
            input_video: Đường dẫn video gốc
            logo_path: Đường dẫn file logo (PNG có alpha hoặc JPEG đều được)
            banner_path: (tương thích ngược) nếu không truyền intro/outro riêng sẽ dùng ảnh này cho cả 2
            output_path: Đường dẫn xuất video
            background_style: 'blur', 'gradient', 'solid'
            banner_intro_path: Ảnh banner dùng cho 20 giây đầu (PNG/JPEG)
            banner_outro_path: Ảnh banner dùng cho 5 giây cuối (PNG/JPEG)
        """
        self.input_video = input_video
        self.logo_path = logo_path
        # Tương thích ngược: nếu không truyền intro/outro riêng, dùng banner_path cho cả hai
        self.banner_intro_path = banner_intro_path or banner_path
        self.banner_outro_path = banner_outro_path or banner_path
        # (Giữ biến cũ nếu nơi khác còn reference)
        self.banner_path = banner_path

        self.output_path = output_path
        self.target_aspect_ratio = 9 / 16  # Tỉ lệ 9:16 cho Shorts
        self.background_style = background_style

    # ============================
    # Pipeline chính
    # ============================
    def process_video(self):
        try:
            print(f"Đang xử lý video: {self.input_video}")

            # Load video gốc
            video = VideoFileClip(self.input_video)
            original_duration = video.duration

            # Giới hạn thời lượng: >180 -> lấy 180s đầu
            if video.duration > 178:
                video = video.subclip(0, 175)
                print(f"Video dài {original_duration:.1f}s, đã cắt xuống 175s")

            # 1) Chèn logo
            video_with_logo = self._add_logo(video)

            # 2) Resize về 9:16 với nền theo style
            video_resized = self._resize_video_to_portrait(video_with_logo)

            # 3) Banner 20 giây đầu
            video_with_intro = self._add_banner_intro(video_resized, duration=20)

            # 4) Banner 5 giây cuối
            final_video = self._add_banner_outro(video_with_intro, duration=5)

            # 5) Xuất file
            print(f"Đang xuất video đến: {self.output_path}")
            final_video.write_videofile(
                self.output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
            )

            # Giải phóng tài nguyên
            video.close()
            final_video.close()

            print("Hoàn thành xử lý video!")
            return {
                "status": "success",
                "input_video": self.input_video,
                "output_video": self.output_path,
                "original_duration": original_duration,
                "final_duration": final_video.duration,
            }

        except Exception as e:
            print(f"Lỗi khi xử lý video: {str(e)}")
            return {"status": "error", "error_message": str(e)}

    # ============================
    # Helpers
    # ============================
    def _make_banner_clip(self, path: str | None, video: VideoFileClip, duration: int):
        """
        Tạo ImageClip banner (JPEG/PNG) full khung video với duration chỉ định.
        Trả về None nếu không có path hoặc file không tồn tại.
        """
        if not path or not os.path.exists(path):
            print(f"Cảnh báo: Không tìm thấy banner tại {path}")
            return None
        banner = ImageClip(path)  # PNG có alpha sẽ trong suốt, JPEG che toàn khung
        banner = banner.resize(newsize=(video.w, video.h)).set_duration(duration)
        return banner

    def _add_banner_intro(self, video: VideoFileClip, duration: int = 20):
        """
        Thêm banner che toàn bộ video trong 'duration' giây đầu
        """
        banner = self._make_banner_clip(self.banner_intro_path, video, duration)
        if banner is None:
            return video

        if video.duration <= duration:
            # Nếu video ngắn hơn duration: phủ banner toàn bộ
            final_video = banner.set_duration(video.duration).set_audio(video.audio)
        else:
            video_after_banner = video.subclip(duration)
            audio_full = video.audio
            final_video = concatenate_videoclips([banner, video_after_banner]).set_audio(
                audio_full
            )

        print(f"Đã thêm banner intro {duration} giây")
        return final_video

    def _add_banner_outro(self, video: VideoFileClip, duration: int = 5):
        """
        Thêm banner che toàn bộ video trong 'duration' giây cuối
        """
        banner = self._make_banner_clip(self.banner_outro_path, video, duration)
        if banner is None:
            return video

        if video.duration <= duration:
            final_video = banner.set_duration(video.duration).set_audio(video.audio)
            print(f"Đã thêm banner outro {duration} giây (video ngắn)")
            return final_video

        video_before = video.subclip(0, video.duration - duration)
        final_video = concatenate_videoclips([video_before, banner]).set_audio(video.audio)

        print(f"Đã thêm banner outro {duration} giây")
        return final_video

    def _add_logo(self, video: VideoFileClip):
        """
        Thêm logo vào góc phải dưới của video (PNG có alpha hoặc JPEG)
        """
        if not self.logo_path or not os.path.exists(self.logo_path):
            print(f"Cảnh báo: Không tìm thấy logo tại {self.logo_path}")
            return video

        # ImageClip không có tham số transparent; PNG có alpha sẽ tự trong suốt
        logo = ImageClip(self.logo_path)

        # Resize logo ~15% chiều rộng khung 9:16 sau khi resize (ở đây dùng theo video hiện tại)
        logo_width = int(video.w * 0.15)
        logo = logo.resize(width=logo_width)

        padding = 15
        logo = logo.set_position(
            (video.w - logo.w - padding, video.h - logo.h - padding)
        ).set_duration(video.duration)

        video_with_logo = CompositeVideoClip([video, logo])
        print("Đã thêm logo vào video")
        return video_with_logo

    def _resize_video_to_portrait(self, video: VideoFileClip):
        """
        Resize video về tỉ lệ 9:16 (portrait) với nền tuỳ chọn (blur/gradient/solid)
        Giữ trọn nội dung video, thêm nền cho phần trống.
        """
        # Kích thước target cho Shorts
        target_width = 1080
        target_height = 1920
        target_ratio = target_width / target_height  # 9:16

        current_ratio = video.w / video.h

        # ===== Tạo background theo style =====
        if self.background_style == "blur":
            background = video.copy()

            # Scale để fill khung
            if current_ratio > target_ratio:
                bg_scale = target_height / video.h
            else:
                bg_scale = target_width / video.w
            background = background.resize(bg_scale * 1.2)  # scale thêm cho blur

            # Crop đúng kích thước
            if background.w > target_width:
                x_offset = int((background.w - target_width) / 2)
                background = background.crop(
                    x1=x_offset, width=target_width, height=target_height
                )
            if background.h > target_height:
                y_offset = int((background.h - target_height) / 2)
                background = background.crop(
                    y1=y_offset, width=target_width, height=target_height
                )

            # Làm tối & blur (downscale rồi upscale)
            background = background.fx(colorx, 0.3)  # tối 70%
            blur_factor = 0.1
            temp_size = (int(background.w * blur_factor), int(background.h * blur_factor))
            background = background.resize(newsize=temp_size).resize(
                newsize=(target_width, target_height)
            )

        elif self.background_style == "gradient":
            # Gradient đơn giản 2 mảng màu
            from moviepy.video.VideoClip import ColorClip

            top_color = ColorClip(
                size=(target_width, target_height // 2), color=(30, 144, 255)
            )  # Dodger Blue
            bottom_color = ColorClip(
                size=(target_width, target_height // 2), color=(138, 43, 226)
            )  # Blue Violet

            top_color = top_color.fx(colorx, 0.8)
            bottom_color = bottom_color.fx(colorx, 0.8)

            background = clips_array([[top_color], [bottom_color]]).set_duration(
                video.duration
            )

        else:  # solid
            from moviepy.video.VideoClip import ColorClip

            background = ColorClip(
                size=(target_width, target_height), color=(135, 206, 235)
            ).set_duration(video.duration)  # Sky Blue

        # ===== Resize video chính để fit trong khung 9:16 =====
        if current_ratio > target_ratio:
            # Video quá rộng -> scale theo width
            new_width = target_width
            new_height = int(target_width / current_ratio)
        else:
            # Video quá cao -> scale theo height
            new_height = target_height
            new_width = int(target_height * current_ratio)

        # Clamp kích thước
        if new_height > target_height:
            scale_factor = target_height / new_height
            new_height = target_height
            new_width = int(new_width * scale_factor)
        if new_width > target_width:
            scale_factor = target_width / new_width
            new_width = target_width
            new_height = int(new_height * scale_factor)

        main_video = video.resize(newsize=(new_width, new_height))

        # Center
        x_pos = int((target_width - new_width) / 2)
        y_pos = int((target_height - new_height) / 2)
        main_video = main_video.set_position((x_pos, y_pos))

        final_video = CompositeVideoClip(
            [background, main_video], size=(target_width, target_height)
        )

        print(
            f"Đã resize video từ {video.w}x{video.h} → {target_width}x{target_height} (9:16)"
        )
        print(f"Video chính: {new_width}x{new_height} | BG style: {self.background_style}")
        return final_video

    def _create_thumbnail(self):
        """
        Tạo thumbnail từ file output (lấy frame ở giây thứ 5)
        """
        video = VideoFileClip(self.output_path)
        frame = video.get_frame(5)
        thumbnail_path = self.output_path.replace(".mp4", "_thumbnail.jpg")

        img = Image.fromarray(frame)
        img.save(thumbnail_path)

        video.close()
        return thumbnail_path


def process_batch_videos(video_folder, logo_path, banner_path, output_folder,
                         banner_intro_path=None, banner_outro_path=None,
                         background_style="blur"):
    """
    Xử lý nhiều video trong một folder (giữ tương thích cũ + hỗ trợ banner intro/outro riêng)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    results = []
    video_extensions = [".mp4", ".avi", ".mov", ".mkv"]

    for filename in os.listdir(video_folder):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            input_path = os.path.join(video_folder, filename)
            output_filename = f"processed_{os.path.splitext(filename)[0]}.mp4"
            output_path = os.path.join(output_folder, output_filename)

            processor = VideoProcessor(
                input_video=input_path,
                logo_path=logo_path,
                banner_path=banner_path,
                output_path=output_path,
                background_style=background_style,
                banner_intro_path=banner_intro_path,
                banner_outro_path=banner_outro_path,
            )
            result = processor.process_video()
            results.append(result)

    return results
