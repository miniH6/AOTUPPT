# gpt_module.py

import os
import requests
import re
import time
from requests.exceptions import ChunkedEncodingError, ReadTimeout, HTTPError

# —— 从环境或 Streamlit Secret 读取 Key ——  
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

def call_openrouter(
    prompt: str,
    model: str = "mistralai/mistral-7b-instruct",
    temperature: float = 0.7,
    max_retries: int = 3,
    timeout: float = 60.0
) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (ChunkedEncodingError, ReadTimeout):
            if attempt < max_retries:
                time.sleep(attempt)
                continue
            raise
        except HTTPError as e:
            raise RuntimeError(f"OpenRouter API error: {e}")

def generate_ppt_outline(
    task: str,
    text_content: str,
    image_paths: list[str],
    language: str = "zh"
) -> list[dict]:
    # 1) 构造初稿大纲 Prompt
    if language == "zh":
        prompt = (
            "你是一名优秀的 PPT 设计师，只能使用中文输出。"
            "请根据下面的主题生成 6~8 页结构化大纲（每页：标题 + 要点列表）：\n"
            f"主题：{task}\n"
            f"参考文字（前1000字）：{text_content[:1000]}"
        )
    else:
        prompt = (
            "You are an expert PowerPoint designer. Output in English only.\n"
            "Based on the topic below, generate a 6–8 slide outline (Title + bullet points):\n"
            f"Topic: {task}\n"
            f"Reference text (first 1000 chars): {text_content[:1000]}"
        )

    raw_outline = call_openrouter(prompt)

    # 2) 正则解析标题与要点
    slide_pattern = re.compile(r"^(?:Slide\s*\d+[:：]|幻灯片\s*\d+[:：]|\d+[\.、])\s*(.+)")
    bullet_pattern = re.compile(r"^(?:[-\*•]|\d+[\.、])\s*(.+)")

    slides_tmp: list[dict] = []
    for line in raw_outline.splitlines():
        ln = line.strip()
        if not ln:
            continue
        m_title = slide_pattern.match(ln)
        if m_title:
            slides_tmp.append({"title": m_title.group(1).strip(), "bullets": []})
            continue
        if slides_tmp:
            m_bullet = bullet_pattern.match(ln)
            if m_bullet:
                slides_tmp[-1]["bullets"].append(m_bullet.group(1).strip())

    # 兜底：若没有任何 slide 标题，则按空行分块
    if not slides_tmp:
        for block in raw_outline.split("\n\n"):
            blk = block.strip()
            if not blk:
                continue
            lines = [l.strip() for l in blk.splitlines() if l.strip()]
            title = lines[0]
            bullets = []
            for l in lines[1:]:
                mb = bullet_pattern.match(l)
                if mb:
                    bullets.append(mb.group(1).strip())
            slides_tmp.append({"title": title, "bullets": bullets})

    # 3) 要点展开 & 合并短页
    slides = []
    buffer = {"title": "", "content": ""}
    limit = 300

    for item in slides_tmp:
        if not item["bullets"]:
            continue
        pts = "\n".join(f"- {b}" for b in item["bullets"])
        if language == "zh":
            exp_prompt = "请用中文将以下要点展开为一段简洁流畅的幻灯片正文：\n" + pts
        else:
            exp_prompt = "Please expand the following bullet points into a concise slide paragraph:\n" + pts

        paragraph = call_openrouter(exp_prompt, temperature=0.6).strip()
        if buffer["content"] and len(buffer["content"]) + len(paragraph) < limit:
            buffer["content"] += "\n" + paragraph
        else:
            if buffer["content"]:
                slides.append(buffer)
            buffer = {"title": item["title"], "content": paragraph}

    if buffer["content"]:
        slides.append(buffer)

    return slides