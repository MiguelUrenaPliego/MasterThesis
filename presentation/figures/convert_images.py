from pathlib import Path
from PIL import Image

folder = Path("/home/miguel/Documents/UNI/Master/2/TFM/presentation/figures")

for ext in ("*.png", "*.jpeg", "*.JPEG"):
    for img_path in folder.glob(ext):
        img = Image.open(img_path).convert("RGB")
        jpg_path = img_path.with_suffix(".jpg")
        img.save(jpg_path, quality=95)