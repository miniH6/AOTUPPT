from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# 自动选择 GPU or CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# 加载 BLIP 模型
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

def vision_caption(image_path: str) -> str:
    """
    使用 BLIP 对图片生成简洁描述
    """
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt").to(device)
        out = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption.strip()
    except Exception as e:
        # 如果出现错误，回退提示
        return f"[BLIP 识别失败: {str(e)}]"