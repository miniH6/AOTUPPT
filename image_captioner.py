import streamlit as st
import requests
import base64

# 尝试导入 vision_caption（本地 BLIP 模型）
try:
    from vision import vision_caption
    vision_available = True
except ImportError:
    vision_available = False

from gpt_module import call_openrouter  # 引入统一的 OpenRouter

def generate_image_caption(image_path: str, language: str = "zh") -> dict:
    """
    根据图片生成幻灯片说明文字
    返回：
    {
        "title": ...,
        "content": ...,
        "extended": ...,
        "image_path": ...,
        "animation": ...
    }
    """

    # —— 1. 优先 BLIP ——  
    caption = None
    if vision_available:
        try:
            caption = vision_caption(image_path)
        except Exception as e:
            st.warning(f"⚠️ 本地图像识别失败，改用大模型：{e}")

    # —— 2. 如果失败用大模型 ——  
    if not caption:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        if language == "zh":
            prompt = f"""
你是一名 PPT 演讲者，请根据以下 Base64 图片片段，为一场演讲编写一个详细且生动的描述，长度 150~200 字，要求：
- 只用自然流畅的中文
- 避免出现“图中显示”、“此图表明”等模板化表述
- 语言应富有情感和细节，像一个人面对观众在描述
- 尽可能提及画面中的色彩、元素、情感氛围
- 突出观众可能感兴趣的细节

请输出一段自然演讲风格：
图片 Base64（前500位）：{img_b64[:500]}
"""
        else:
            prompt = f"""
You are a professional PowerPoint presenter. Based on the following Base64 image snippet, please write a vivid and engaging English description suitable for a live audience, about 100–150 words, with these requirements:
- Use fluent, natural English
- Avoid phrases like “this image shows” or “this picture illustrates”
- Add emotional color and detailed elements, as if speaking to people
- Mention colors, visual elements, atmosphere if possible
- Highlight details that the audience might care about

Base64 (first 500 chars): {img_b64[:500]}
"""
        caption = call_openrouter(prompt, temperature=0.5)

    caption = caption.strip()

    # —— 3. 生成拓展说明 ——  
    if language == "zh":
        ext_prompt = f"""
请将以下简要说明扩展成一段流畅的 PPT 演讲文字，约 200~300 字：
{caption}
"""
    else:
        ext_prompt = f"""
Please expand the following caption into a fluent presentation paragraph (~150–200 words):
{caption}
"""
    extended = call_openrouter(ext_prompt, temperature=0.6).strip()

    # —— 4. 自动推荐动画 ——  
    ani_prompt = (
        f"根据以下图片描述，请推荐一个适合 PPT 中使用的动画效果（例如飞入、放大、渐显），只返回动画名称：\n{caption}"
        if language == "zh"
        else f"Based on the following caption, suggest one PowerPoint animation (e.g. fly-in, fade, zoom), only return animation name:\n{caption}"
    )
    animation = call_openrouter(ani_prompt, temperature=0.3).strip()

    # —— 5. 标题 ——  
    title = "图片说明" if language == "zh" else "Image Description"

    return {
        "title": title,
        "content": caption[:100],       # 图页底部简要
        "extended": extended,           # 拓展页正文
        "image_path": image_path,
        "animation": animation
    }