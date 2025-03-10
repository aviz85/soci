#!/usr/bin/env python
import os
from PIL import Image, ImageDraw, ImageFont

# Create a simple icon
size = 64
img = Image.new('RGB', (size, size), color=(74, 118, 168))  # #4a76a8 blue
draw = ImageDraw.Draw(img)

# Draw a white 'S'
try:
    # Try to load a font, fall back to default if not available
    font = ImageFont.truetype("Arial.ttf", 36)
except IOError:
    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFNSText.ttf", 36)
    except:
        font = ImageFont.load_default()

# Draw text in the center
draw.text((size/2, size/2), "S", fill="white", font=font, anchor="mm")

# Save as SVG for future use (if needed)
svg_path = os.path.join('static', 'favicon.svg')
print(f"Note: SVG creation skipped (requires additional libraries)")

# Save as PNG
png_path = os.path.join('static', 'favicon.png')
img.save(png_path)
print(f"Created PNG file at {png_path}")

# Save as ICO 
ico_path = os.path.join('static', 'favicon.ico')
img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (64, 64)])
print(f"Created ICO file at {ico_path}") 