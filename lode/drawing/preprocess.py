"""Optional OpenCV image enhancement for OCR. It does not infer drawing geometry."""
from io import BytesIO

def enhance_for_ocr(image_bytes: bytes) -> bytes:
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("OpenCV enhancement dependencies are unavailable. Install requirements.txt.") from exc
    image=Image.open(BytesIO(image_bytes)).convert("RGB")
    arr=np.array(image)
    gray=cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)
    denoised=cv2.fastNlMeansDenoising(gray,None,10,7,21)
    enhanced=cv2.adaptiveThreshold(denoised,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,11)
    ok,encoded=cv2.imencode(".png",enhanced)
    if not ok: raise RuntimeError("OpenCV could not encode the enhanced image.")
    return encoded.tobytes()
