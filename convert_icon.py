"""
Convert logo.png to high-quality ICO format for application icon
"""
from PIL import Image as PILImage
import os

# Open the PNG image
img_path = os.path.join(os.path.dirname(__file__), 'img', 'logo.png')
ico_path = os.path.join(os.path.dirname(__file__), 'img', 'logo.ico')

# Open and convert to ICO with multiple sizes for high quality
img = PILImage.open(img_path)

# Create different sizes for the icon (including high-res sizes)
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (192, 192), (256, 256)]
ico_images = []

for size in sizes:
    # Resize image with high-quality resampling
    resized = img.resize(size, PILImage.Resampling.LANCZOS)
    ico_images.append(resized)

# Save as ICO with all sizes for best quality
ico_images[0].save(ico_path, format='ICO', sizes=[(size[0], size[1]) for size in sizes])

print(f"High-quality icon created successfully: {ico_path}")
