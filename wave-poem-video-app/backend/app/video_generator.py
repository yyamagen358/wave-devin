import os
import random
import re
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
        self.fps = 30
        self.slide_duration = 4
        
    def parse_poem(self, poem_path: str) -> Tuple[str, List[str]]:
        with open(poem_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        title = Path(poem_path).stem
        title = re.sub(r'^\d+', '', title)
        
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
        for para in paragraphs:
            formatted = self.format_text_for_display(para)
            formatted_paragraphs.append(formatted)
        
        return title, formatted_paragraphs
    
    def format_text_for_display(self, text: str, max_chars_per_line: int = 14) -> str:
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) <= max_chars_per_line:
                formatted_lines.append(line)
            else:
                for i in range(0, len(line), max_chars_per_line):
                    formatted_lines.append(line[i:i+max_chars_per_line])
        
        return '\n'.join(formatted_lines)
    
    def create_text_image(self, text: str, bg_image_path: str, 
                         font_size: int = 80, is_title: bool = False) -> Image.Image:
        bg = Image.open(bg_image_path).convert('RGBA')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        txt_layer = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
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
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
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
    
    def create_scrolling_text_image(self, full_text: str, bg_image_path: str) -> Image.Image:
        bg = Image.open(bg_image_path).convert('RGBA')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        scroll_height = self.height * 3
        txt_layer = Image.new('RGBA', (self.width, scroll_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        lines = full_text.split('\n')
        y = scroll_height - 200
        
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 180))
                draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
                
                y -= 80
        
        combined = Image.alpha_composite(bg, txt_layer.crop((0, 0, self.width, self.height)))
        return combined.convert('RGB')
    
    def get_random_images(self, count: int) -> List[str]:
        image_files = list(self.image_dir.glob("*.jpg")) + list(self.image_dir.glob("*.png"))
        
        if not image_files:
            raise ValueError("No images found in image directory")
        
        return [str(random.choice(image_files)) for _ in range(count)]
    
    def generate_video(self, poem_path: str) -> str:
        title, paragraphs = self.parse_poem(poem_path)
        
        num_slides = 1 + len(paragraphs) + 1
        images = self.get_random_images(num_slides)
        
        clips = []
        
        title_img = self.create_title_image(title, images[0])
        title_img_path = self.output_dir / "temp_title.jpg"
        title_img.save(title_img_path)
        title_clip = ImageClip(str(title_img_path), duration=self.slide_duration)
        clips.append(title_clip)
        
        for i, paragraph in enumerate(paragraphs):
            para_img = self.create_text_image(paragraph, images[i+1])
            para_img_path = self.output_dir / f"temp_para_{i}.jpg"
            para_img.save(para_img_path)
            para_clip = ImageClip(str(para_img_path), duration=self.slide_duration)
            clips.append(para_clip)
        
        with open(poem_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        full_text = re.sub(r'^\d+', '', full_text, flags=re.MULTILINE)
        
        end_img = self.create_scrolling_text_image(full_text, images[-1])
        end_img_path = self.output_dir / "temp_end.jpg"
        end_img.save(end_img_path)
        end_clip = ImageClip(str(end_img_path), duration=6)
        clips.append(end_clip)
        
        video = concatenate_videoclips(clips, method="compose")
        
        if self.bgm_path.exists():
            audio = AudioFileClip(str(self.bgm_path))
            audio = audio.subclipped(0, min(audio.duration, video.duration))
            fade_in = afx.AudioFadeIn(1.0)
            fade_out = afx.AudioFadeOut(1.0)
            audio = audio.with_effects([fade_in, fade_out])
            video = video.with_audio(audio)
        
        video = video.with_fps(self.fps)
        
        output_filename = f"{title}.mp4"
        output_path = self.output_dir / output_filename
        
        video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=self.fps,
            preset='medium',
            logger=None
        )
        
        for temp_file in self.output_dir.glob("temp_*.jpg"):
            temp_file.unlink()
        
        video.close()
        if self.bgm_path.exists():
            audio.close()
        
        return output_filename
