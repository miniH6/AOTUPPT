import streamlit as st
import requests
import base64
import re

def generate_image_caption(image_path: str, language: str = "zh") -> dict:
    """
    根据图片生成一页幻灯片的说明文字（标题 + 内容）
    """
    # 读取并转 Base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    # 1. 构造 prompt
    if language == "zh":
        prompt = f"""
你是一位优秀的 PPT 演讲者。请根据下面的图片（以 Base64 编码给出），撰写一页幻灯片的说明文字：

要求：
- 标题一句话，突出重点
- 正文约 50~100 字，自然流畅，像人在讲述
- 避免“图中显示”、“该图为”等模板句式

格式：
标题：xxx
内容：xxx

图片 Base64（前500位）：
{img_b64[:500]}
"""
    else:
        prompt = f"""
You are an expert presenter preparing a PowerPoint slide with an image. Please write a title and a short natural explanation for the image (Base64 preview below):

Requirements:
- Title: one sentence summarizing the message
- Content: ~50-100 words, human-like tone
- Avoid "This image shows..." or mechanical descriptions

Format:
Title: xxx
Content: xxx

Image Base64 (first 500 chars):
{img_b64[:500]}
"""

    # 2. 调用 OpenRouter
    url = "https://openrouter.ai/api/v1/chat/completions"
    key = st.secrets["openrouter_key"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
    }

    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    # 3. 解析输出
    title, desc = (
        ("图片说明", "") if language == "zh" else ("Image Explanation", "")
    )
    if language == "zh":
        m = re.search(r"标题[:：](.+)\n内容[:：](.+)", content, re.S)
        if m:
            title = m.group(1).strip()
            desc = m.group(2).strip()
        else:
            desc = content
        desc = desc[:100]
    else:
        m = re.search(r"Title[:：](.+)\nContent[:：](.+)", content, re.S)
        if m:
            title = m.group(1).strip()
            desc = m.group(2).strip()
        else:
            desc = content
        desc = " ".join(desc.split()[:100])

    return {"title": title, "content": desc}