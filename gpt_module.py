import requests
import re
import time
from requests.exceptions import ChunkedEncodingError, ReadTimeout, HTTPError
import streamlit as st

def call_openrouter(
    prompt: str,
    model: str = "mistralai/mistral-7b-instruct",
    temperature: float = 0.7,
    max_retries: int = 3,
    timeout: float = 60.0
) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    key = st.secrets["openrouter_key"]
    headers = {
        "Authorization": f"Bearer {key}",
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
        except HTTPError:
            raise

def generate_ppt_outline(
    task: str,
    text: str,
    image_paths: list,
    language: str = "zh",
    style: str = "正式"
) -> list[dict]:
    """
    新增 style 参数：
    可选值如：
    - "正式"
    - "幽默"
    - "儿童"
    - "新闻播音员"
    - "古风"
    """
    style_zh = {
        "正式": "正式理性",
        "幽默": "幽默风趣",
        "儿童": "儿童易懂",
        "新闻播音员": "新闻主播风格",
        "古风": "古代文风"
    }
    style_en = {
        "formal": "formal academic",
        "humorous": "humorous",
        "child": "child-friendly",
        "news": "news anchor style",
        "classical": "classical writing"
    }
    style_prompt = style_zh.get(style, "正式理性") if language == "zh" else style_en.get(style, "formal")

    # 主题
    if language == "zh":
        prompt = (
            f"你是一名优秀的 PPT 设计师，请使用【{style_prompt}】风格，只能使用中文输出。"
            f"请根据下面主题生成 6~8 页结构化大纲（每页：标题 + 要点列表）：\n"
            f"主题：{task}\n"
            f"参考文字（前1000字）：{text[:1000]}"
        )
    else:
        prompt = (
            f"You are a great PowerPoint designer. Please use a {style_prompt} style, output in English only. "
            f"Based on the topic below, generate a 6–8 slide outline (each slide: Title + bullet points):\n"
            f"Topic: {task}\n"
            f"Reference text (first 1000 chars): {text[:1000]}"
        )

    raw_outline = call_openrouter(prompt)
    slides = []

    for line in raw_outline.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(?:Slide\s*\d+[:：]|幻灯片\s*\d+[:：]|\d+[\.、])\s*(.+)$", line)
        if m:
            slides.append({"title": m.group(1).strip(), "bullets": [], "content": ""})
        elif slides and re.match(r"^(?:[-\*•]|\d+[\.、])\s+", line):
            point = re.sub(r"^(?:[-\*•]|\d+[\.、])\s*", "", line).strip()
            slides[-1]["bullets"].append(point)

    merged = []
    buf = {"title": "", "content": ""}
    char_limit = 300

    for s in slides:
        if not s["bullets"]:
            continue
        pts = "\n".join(s["bullets"])

        exp_prompt = (
            f"请用【{style_prompt}】风格将以下要点展开为一段简洁流畅的幻灯片正文：\n{pts}"
            if language == "zh"
            else f"Please expand the following bullet points into a concise slide paragraph in {style_prompt} style:\n{pts}"
        )
        paragraph = call_openrouter(exp_prompt, temperature=0.6).strip()

        fact_prompt = (
            f"请基于这段内容，补充一条与主题相关的可靠知识（如来源、数据、人物、时间等），100字内：\n{paragraph}"
            if language == "zh"
            else f"Based on this content, add one related factual knowledge or data citation in 1 sentence:\n{paragraph}"
        )
        fact = call_openrouter(fact_prompt, temperature=0.5).strip()

        enriched = paragraph + ("\n\n📌 " + fact if fact else "")

        if buf["content"] and len(buf["content"]) + len(enriched) < char_limit:
            buf["content"] += "\n" + enriched
        else:
            if buf["content"]:
                merged.append(buf)
            buf = {"title": s["title"], "content": enriched}

    if buf["content"]:
        merged.append(buf)
    return merged