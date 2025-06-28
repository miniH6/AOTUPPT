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
    """
    统一 GPT 接口
    """
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
    生成 PPT 大纲 + 正文
    """
    style_zh = {
        "正式": "正式理性",
        "幽默": "幽默风趣",
        "儿童": "儿童易懂",
        "新闻播音员": "新闻播报",
        "古风": "古代文风",
        "商务路演": "商务路演",
        "TED": "TED风格",
        "小红书": "小红书口吻"
    }
    style_en = {
        "formal": "formal academic",
        "humorous": "humorous",
        "child": "child-friendly",
        "news": "news anchor style",
        "classical": "classical style",
        "business": "business pitch",
        "TED": "TED talk style",
        "xiaohongshu": "influencer style"
    }
    style_prompt = style_zh.get(style, "正式理性") if language == "zh" else style_en.get(style, "formal")

    # 主题
    if language == "zh":
        prompt = (
            f"你是一名专业 PPT 设计师，请用【{style_prompt}】风格，只用中文输出。"
            f"请为以下主题生成 6~8 页结构化大纲（每页：标题 + 要点列表），"
            f"不要出现任何词汇注释、翻译、解释，只输出自然流畅文字，"
            f"并且请为每页推荐一个适合的 PPT 动画效果（如：淡入、飞入、擦除）：\n"
            f"主题：{task}\n"
            f"参考文字（前1000字）：{text[:1000]}"
        )
    else:
        prompt = (
            f"You are a professional PowerPoint designer. Use a {style_prompt} style, output in English only. "
            f"Generate a 6–8 slide outline (each slide: Title + bullet points). "
            f"Do not include word-level translations or explanations, only fluent natural paragraphs, "
            f"and please recommend one animation for each slide (e.g., fade, fly-in, wipe):\n"
            f"Topic: {task}\n"
            f"Reference text (first 1000 chars): {text[:1000]}"
        )

    raw_outline = call_openrouter(prompt)
    slides = []

    current_animation = None

    for line in raw_outline.splitlines():
        line = line.strip()
        if not line:
            continue
        # 匹配幻灯片标题
        m = re.match(r"^(?:Slide\s*\d+[:：]|幻灯片\s*\d+[:：]|\d+[\.、])\s*(.+)$", line)
        if m:
            slides.append({"title": m.group(1).strip(), "bullets": [], "content": "", "animation": None})
        elif slides and re.match(r"^(?:[-\*•]|\d+[\.、])\s+", line):
            point = re.sub(r"^(?:[-\*•]|\d+[\.、])\s*", "", line).strip()
            slides[-1]["bullets"].append(point)
        elif "动画" in line or "animation" in line:
            current_animation = line

    merged = []
    buf = {"title": "", "content": "", "animation": None}
    char_limit = 300

    for s in slides:
        if not s["bullets"]:
            continue
        pts = "\n".join(s["bullets"])

        exp_prompt = (
            f"请用【{style_prompt}】风格将以下要点展开为流畅自然的幻灯片正文，不要包含词汇注释或翻译：\n{pts}"
            if language == "zh"
            else f"Please expand the following bullet points into a fluent slide paragraph in {style_prompt} style. "
                 f"Do not include word explanations or translations:\n{pts}"
        )
        paragraph = call_openrouter(exp_prompt, temperature=0.6).strip()

        fact_prompt = (
            f"请基于该幻灯片正文，补充一句可靠相关知识（数据、来源、人名），100字以内：\n{paragraph}"
            if language == "zh"
            else f"Based on this paragraph, add one related factual knowledge or citation (source, data, person) within 1 sentence:\n{paragraph}"
        )
        fact = call_openrouter(fact_prompt, temperature=0.5).strip()

        enriched = paragraph + ("\n\n📌 " + fact if fact else "")

        # 合并逻辑
        if buf["content"] and len(buf["content"]) + len(enriched) < char_limit:
            buf["content"] += "\n" + enriched
        else:
            if buf["content"]:
                merged.append(buf)
            buf = {"title": s["title"], "content": enriched, "animation": s.get("animation") or current_animation}

    if buf["content"]:
        merged.append(buf)
    return merged