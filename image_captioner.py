import streamlit as st
import requests
import base64
import re

# 尝试导入 vision_caption（本地 BLIP 模型）
try:
    from vision import vision_caption
    vision_available = True
except ImportError:
    vision_available = False

from gpt_module import call_openrouter  # 引入同样的 OpenRouter 调用接口

def generate_image_caption(image_path: str, language: str = "zh") -> dict:
    """
    根据图片生成一页幻灯片说明文字（标题 + 简要内容），并附加拓展解释段落
    返回格式：
    {
        "title": ...,          # 幻灯片标题
        "content": ...,        # 简要说明，用于图页底部
        "extended": ...,       # 拓展说明，单独成页
        "image_path": ...      # 原图路径，用于添加图片
    }
    """
    # —— 1. 首先尝试本地模型 BLIP 获取简要说明 ——  
    caption = None
    if vision_available:
        try:
            caption = vision_caption(image_path)
        except Exception as e:
            st.warning(f"⚠️ 本地图像识别失败，回退 OpenRouter：{e}")

    # —— 2. 若失败则使用 OpenRouter 图像描述 ——  
    if not caption:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        if language == "zh":
            prompt = f"""
你是一位 PPT 演讲者，请根据下面的图片（Base64 编码片段）自然描述其内容，避免模板句式（如“图中显示”等）：
图片 Base64（前500位）：{img_b64[:500]}
"""
        else:
            prompt = f"""
You are a PowerPoint presenter. Please write a natural description of the following image, without saying "this image shows":
Image Base64 (first 500 chars): {img_b64[:500]}
"""
        caption = call_openrouter(prompt, temperature=0.5)

    caption = caption.strip()[:100]

    # —— 3. 拓展内容生成 ——  
    if language == "zh":
        ext_prompt = f"请将以下图片说明扩展为一段完整自然的解释性文本，150~200字：\n{caption}"
    else:
        ext_prompt = f"Please expand the following image caption into a coherent explanation (~100-150 words):\n{caption}"

    extended = call_openrouter(ext_prompt, temperature=0.7).strip()

    # —— 4. 标题生成 ——  
    title = "图片说明" if language == "zh" else "Image Description"

    return {
        "title": title,
        "content": caption,
        "extended": extended,
        "image_path": image_path
    }