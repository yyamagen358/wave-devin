import os
import random
import re
import gc
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip, 
    TextClip, 
    CompositeVideoClip, 
    AudioFileClip,
    concatenate_videoclips,
    afx
)

class VideoGenerator:
    def __init__(self, image_dir: str, bgm_path: str, output_dir: str):
        self.image_dir = Path(image_dir)
        self.bgm_path = Path(bgm_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.width = 1080
        self.height = 1920
        self.fps = 24
        self.slide_duration = 6
        
        self.japanese_font_path = self._find_japanese_font()
        print(f"[DEBUG] VideoGenerator initialized")
        print(f"[DEBUG] - Font: {self.japanese_font_path}")
        print(f"[DEBUG] - BGM path: {self.bgm_path}")
        print(f"[DEBUG] - BGM exists: {self.bgm_path.exists()}")
        print(f"[DEBUG] - Image dir: {self.image_dir}")
        print(f"[DEBUG] - Output dir: {self.output_dir}")
    
    def _find_japanese_font(self) -> str:
        """Find a Japanese font on the system"""
        import platform
        import sys
        
        system = platform.system()
        
        if system == "Windows":
            windows_fonts = [
                "C:\\Windows\\Fonts\\msgothic.ttc",  # MS Gothic
                "C:\\Windows\\Fonts\\meiryo.ttc",     # Meiryo
                "C:\\Windows\\Fonts\\yugothic.ttf",   # Yu Gothic
                "C:\\Windows\\Fonts\\YuGothM.ttc",    # Yu Gothic Medium
            ]
            for font in windows_fonts:
                if Path(font).exists():
                    print(f"[DEBUG] Found Windows font: {font}")
                    return font
        elif system == "Darwin":
            mac_fonts = [
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/Library/Fonts/Osaka.ttf",
            ]
            for font in mac_fonts:
                if Path(font).exists():
                    return font
        else:
            linux_fonts = [
                "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
                "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
            ]
            for font in linux_fonts:
                if Path(font).exists():
                    return font
        
        print("[WARNING] No Japanese font found, using default font")
        return None
    
    def _get_bgm_path(self) -> Path:
        """Dynamically check for BGM file at generation time"""
        bgm_dir = self.bgm_path.parent
        
        bgm_mp3 = bgm_dir / "BGM.mp3"
        if bgm_mp3.exists():
            print(f"[DEBUG] Found BGM.mp3")
            return bgm_mp3
        
        bgm_poem_mp3 = bgm_dir / "bgm_poem.mp3"
        if bgm_poem_mp3.exists():
            print(f"[DEBUG] Found bgm_poem.mp3")
            return bgm_poem_mp3
        
        print(f"[WARNING] No BGM file found in {bgm_dir}")
        return self.bgm_path
        
    def parse_poem(self, poem_path: str) -> Tuple[str, List[str], List[str]]:
        with open(poem_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n')]
        
        title = Path(poem_path).stem
        title = re.sub(r'^\d+', '', title).strip()
        if not title:
            title = "無題"
        
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            if line.startswith('《') or line.startswith('「'):
                continue
            
            if re.match(r'^\d+', line):
                line = re.sub(r'^\d+', '', line)
            
            if not line:
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        if current_paragraph:
            paragraphs.append('\n'.join(current_paragraph))
        
        formatted_paragraphs = []
        raw_formatted_paragraphs = []
        for para in paragraphs:
            formatted = self.format_text_for_display(para, add_spacing=True)
            raw_formatted = self.format_text_for_display(para, add_spacing=False)
            formatted_paragraphs.append(formatted)
            raw_formatted_paragraphs.append(raw_formatted)
        
        return title, formatted_paragraphs, raw_formatted_paragraphs
    
    def format_text_for_display(self, text: str, max_chars_per_line: int = 11, add_spacing: bool = True) -> str:
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) <= max_chars_per_line:
                formatted_lines.append(line)
            else:
                for i in range(0, len(line), max_chars_per_line):
                    formatted_lines.append(line[i:i+max_chars_per_line])
        
        if add_spacing:
            spaced_lines = []
            for i, line in enumerate(formatted_lines):
                spaced_lines.append(line)
                if (i + 1) % 2 == 0 and i < len(formatted_lines) - 1:
                    spaced_lines.append('')
            return '\n'.join(spaced_lines)
        
        return '\n'.join(formatted_lines)
    
    def create_text_image(self, text: str, bg_image_path: str, 
                         font_size: int = 60, is_title: bool = False) -> Image.Image:
        bg = Image.open(bg_image_path).convert('RGBA')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        txt_layer = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            if self.japanese_font_path and Path(self.japanese_font_path).exists():
                font = ImageFont.truetype(self.japanese_font_path, font_size)
                print(f"[DEBUG] Loaded font: {self.japanese_font_path} at size {font_size}")
            else:
                print(f"[ERROR] Font path not found: {self.japanese_font_path}")
                font = ImageFont.load_default()
        except Exception as e:
            print(f"[ERROR] Failed to load font: {e}")
            font = ImageFont.load_default()
        
        lines = text.split('\n')
        
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
        
        total_height = sum(line_heights) + (len(lines) - 1) * 20
        
        y = (self.height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            
            draw.text((x+3, y+3), line, font=font, fill=(0, 0, 0, 180))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            
            y += line_heights[i] + 20
        
        combined = Image.alpha_composite(bg, txt_layer)
        return combined.convert('RGB')
    
    def create_title_image(self, title: str, bg_image_path: str) -> Image.Image:
        bg = Image.open(bg_image_path).convert('RGBA')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        txt_layer = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            if self.japanese_font_path and Path(self.japanese_font_path).exists():
                title_font = ImageFont.truetype(self.japanese_font_path, 90)
                subtitle_font = ImageFont.truetype(self.japanese_font_path, 60)
                print(f"[DEBUG] Loaded title fonts from: {self.japanese_font_path}")
            else:
                print(f"[ERROR] Font path not found for title: {self.japanese_font_path}")
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
        except Exception as e:
            print(f"[ERROR] Failed to load title fonts: {e}")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        main_title = "無条件の波動"
        
        bbox1 = draw.textbbox((0, 0), main_title, font=subtitle_font)
        w1 = bbox1[2] - bbox1[0]
        x1 = (self.width - w1) // 2
        y1 = self.height // 2 - 150
        
        draw.text((x1+3, y1+3), main_title, font=subtitle_font, fill=(0, 0, 0, 180))
        draw.text((x1, y1), main_title, font=subtitle_font, fill=(255, 255, 255, 255))
        
        bbox2 = draw.textbbox((0, 0), title, font=title_font)
        w2 = bbox2[2] - bbox2[0]
        x2 = (self.width - w2) // 2
        y2 = y1 + 120
        
        draw.text((x2+3, y2+3), title, font=title_font, fill=(0, 0, 0, 180))
        draw.text((x2, y2), title, font=title_font, fill=(255, 255, 255, 255))
        
        combined = Image.alpha_composite(bg, txt_layer)
        return combined.convert('RGB')
    
    def create_scrolling_clip(self, full_text: str, bg_image_path: str):
        from moviepy import vfx
        
        bg = Image.open(bg_image_path).convert('RGBA')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        try:
            if self.japanese_font_path and Path(self.japanese_font_path).exists():
                font = ImageFont.truetype(self.japanese_font_path, 60)
                print(f"[DEBUG] Loaded scrolling font from: {self.japanese_font_path}")
            else:
                print(f"[ERROR] Font path not found for scrolling: {self.japanese_font_path}")
                font = ImageFont.load_default()
        except Exception as e:
            print(f"[ERROR] Failed to load scrolling font: {e}")
            font = ImageFont.load_default()
        
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        formatted_lines = []
        for i, line in enumerate(lines):
            formatted_lines.append(line)
            if (i + 1) % 2 == 0:
                formatted_lines.append('')
        
        lines = list(reversed(formatted_lines))
        
        line_height = 80
        num_lines = len(lines)
        duration = max(20, int(num_lines * 1.5))
        
        total_text_height = num_lines * line_height + self.height
        
        scroll_height = total_text_height + self.height
        txt_layer = Image.new('RGBA', (self.width, scroll_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        y = scroll_height - self.height
        for line in lines:
            if line:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 180))
                draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            
            y -= line_height
        
        def make_frame(t):
            import numpy as np
            progress = t / duration
            scroll_y = int(progress * (total_text_height))
            
            frame = bg.copy()
            crop_y = min(scroll_y, scroll_height - self.height)
            text_crop = txt_layer.crop((0, crop_y, self.width, crop_y + self.height))
            frame = Image.alpha_composite(frame, text_crop)
            
            return np.array(frame.convert('RGB'))
        
        from moviepy import VideoClip
        clip = VideoClip(make_frame, duration=duration)
        return clip.with_fps(self.fps)
    
    def get_random_images(self, count: int) -> List[str]:
        """
        画像プールからランダムに画像を選択します。
        同じ画像が複数回選ばれる可能性があります（画像再利用）。
        
        利点：
        - 少数の画像で多数の動画を生成可能
        - アップロード作業が大幅に削減
        
        例：7枚の画像で10個の動画を生成可能
        
        Args:
            count: 必要な画像の数
            
        Returns:
            ランダムに選ばれた画像パスのリスト
        """
        image_files = list(self.image_dir.glob("*.jpg")) + list(self.image_dir.glob("*.png"))
        
        if not image_files:
            raise ValueError("No images found in image directory")
        
        return [str(random.choice(image_files)) for _ in range(count)]
    
    def generate_video(self, poem_path: str) -> str:
        title, paragraphs, raw_paragraphs = self.parse_poem(poem_path)
        
        num_slides = 1 + len(paragraphs) + 1
        images = self.get_random_images(num_slides)
        
        clips = []
        
        title_img = self.create_title_image(title, images[0])
        title_img_path = self.output_dir / "temp_title.jpg"
        title_img.save(title_img_path, quality=85, optimize=True)
        del title_img
        gc.collect()
        title_clip = ImageClip(str(title_img_path), duration=self.slide_duration)
        clips.append(title_clip)
        
        for i, paragraph in enumerate(paragraphs):
            para_img = self.create_text_image(paragraph, images[i+1])
            para_img_path = self.output_dir / f"temp_para_{i}.jpg"
            para_img.save(para_img_path, quality=85, optimize=True)
            del para_img
            gc.collect()
            para_clip = ImageClip(str(para_img_path), duration=self.slide_duration)
            clips.append(para_clip)
        
        full_text = '\n\n'.join(raw_paragraphs)
        
        end_clip = self.create_scrolling_clip(full_text, images[-1])
        clips.append(end_clip)
        
        video = concatenate_videoclips(clips, method="compose")
        print(f"[DEBUG] Video duration: {video.duration}s")
        
        bgm_file = self._get_bgm_path()
        if bgm_file.exists():
            print(f"[DEBUG] Loading BGM from: {bgm_file}")
            try:
                audio = AudioFileClip(str(bgm_file))
                print(f"[DEBUG] BGM duration: {audio.duration}s")
                if audio.duration < video.duration:
                    print(f"[DEBUG] Looping BGM to match video duration")
                    audio = audio.with_effects([afx.AudioLoop(duration=video.duration)])
                audio = audio.subclipped(0, video.duration)
                fade_in = afx.AudioFadeIn(1.0)
                fade_out = afx.AudioFadeOut(3.0)
                audio = audio.with_effects([fade_in, fade_out])
                video = video.with_audio(audio)
                print(f"[DEBUG] BGM successfully added to video")
            except Exception as e:
                print(f"[ERROR] Failed to add BGM: {e}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
        else:
            print(f"[WARNING] BGM file not found: {bgm_file}")
        
        video = video.with_fps(self.fps)
        
        output_filename = f"{title}.mp4"
        output_path = self.output_dir / output_filename
        
        video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=self.fps,
            preset='fast',  # Changed from 'medium' to 'fast' to reduce memory
            logger=None,
            threads=2  # Limit threads to reduce memory usage
        )
        
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        
        video.close()
        if 'audio' in locals():
            audio.close()
        
        for temp_file in self.output_dir.glob("temp_*.jpg"):
            try:
                temp_file.unlink()
            except:
                pass
        
        del video
        del clips
        gc.collect()
        
        return output_filename
