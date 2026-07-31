import os
from PIL import Image

assets_dir = r"c:\code\python\RsmfInspector\assets"
black_logo_path = os.path.join(assets_dir, "pageone-logo.png")
white_logo_path = os.path.join(assets_dir, "pageone-logo-white.png")

img = Image.open(black_logo_path).convert("RGBA")
data = img.getdata()

new_data = []
for item in data:
    # Change non-transparent black pixels to white (255, 255, 255, alpha)
    if item[3] > 0:  # Has alpha
        new_data.append((255, 255, 255, item[3]))
    else:
        new_data.append(item)

img.putdata(new_data)
img.save(white_logo_path, "PNG")
print(f"Successfully generated white logo at: {white_logo_path}")
