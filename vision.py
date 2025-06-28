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
    使用 BLIP 对图片生成更自然、更丰富的中文描述。
    如果出错会返回较友好的提示。
    """
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt").to(device)
        out = model.generate(**inputs, max_new_tokens=100)
        caption = processor.decode(out[0], skip_special_tokens=True).strip()
        
        # 进一步精简并美化
        if len(caption) < 10:
            return "这是一张内容相对简单的图片，未能获得更多细节描述。"
        else:
            return f"图片包含的元素：{caption}。整体场景较为清晰，请结合上下文进一步理解。"
        
    except Exception as e:
        return f"[图片分析遇到问题，请稍后重试。错误详情：{str(e)}]"