import random
import string
from PIL import Image, ImageDraw, ImageFont
import io
import os

class CaptchaGenerator:
    def __init__(self, length=6, width=200, height=100):
        self.length = length
        self.width = width
        self.height = height
        self.characters = string.ascii_uppercase + string.digits
    
    def generate_captcha(self):
        """Generate a random captcha string"""
        return ''.join(random.choices(self.characters, k=self.length))
    
    def create_image(self, captcha_text):
        """Create a captcha image from text"""
        # Create image with white background
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add noise lines
        for _ in range(5):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill='gray', width=1)
        
        # Add noise dots
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill='gray')
        
        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Draw text with random colors and positions
        text_color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        
        # Add slight rotation and noise to text rendering
        x_offset = (self.width - len(captcha_text) * 25) // 2
        y_offset = (self.height - 40) // 2
        
        for i, char in enumerate(captcha_text):
            x = x_offset + i * 25 + random.randint(-5, 5)
            y = y_offset + random.randint(-5, 5)
            draw.text((x, y), char, font=font, fill=text_color)
        
        return img
    
    def generate_with_image(self):
        """Generate captcha text and image"""
        captcha_text = self.generate_captcha()
        img = self.create_image(captcha_text)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return captcha_text, img_bytes
