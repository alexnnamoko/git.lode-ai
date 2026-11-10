"""Optional explicit CLIP ViT-B/32 image encoder diagnostics.

This encoder produces image embeddings and text-image similarity scores. Similarity is not
proof of object detection or engineering correctness.
"""
from __future__ import annotations
import hashlib
from functools import lru_cache
from io import BytesIO

MODEL_ID = "openai/clip-vit-base-patch32"

@lru_cache(maxsize=1)
def load_clip():
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise RuntimeError("CLIP dependencies are not installed. Run: pip install -r requirements-vision.txt") from exc
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    model = CLIPModel.from_pretrained(MODEL_ID)
    model.eval()
    return torch, processor, model


def encode_image(image_bytes: bytes) -> dict:
    from PIL import Image
    torch, processor, model = load_clip()
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
    vector = features[0].cpu().numpy()
    return {
        "model": MODEL_ID,
        "embedding_dimension": int(vector.shape[0]),
        "embedding_norm": float((vector ** 2).sum() ** 0.5),
        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "embedding_preview": [round(float(x), 6) for x in vector[:12]],
        "status": "PASS — image encoded; this does not prove engineering-object recognition.",
    }


def compare_image_text(image_bytes: bytes, prompts: list[str]) -> list[dict]:
    from PIL import Image
    torch, processor, model = load_clip()
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = outputs.logits_per_image.softmax(dim=1)[0].cpu().tolist()
    return [{"candidate": p, "relative_similarity": round(float(s), 4)} for p, s in sorted(zip(prompts, scores), key=lambda x: x[1], reverse=True)]
