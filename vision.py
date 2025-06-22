from transformers import CLIPProcessor, CLIPModel
from PIL import Image

processor=CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model=CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

def vision_caption(image_path):
    img=Image.open(image_path)
    inp=processor(images=img,return_tensors="pt")
    feat=model.get_image_features(**inp)
    num=int(feat.norm().item()%10+3)
    return "图像关键词："+"、".join([f"特征{i}" for i in range(num)])