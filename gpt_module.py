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


def enforce_chinese(text: str) -> str:
    """
    如果文字中中文比例小于 20%，自动请求 GPT 二次翻译成中文
    并且禁止词汇注释
    """
    zh_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_count = len(text)
    ratio = zh_count / total_count if total_count else 0

    if ratio >= 0.2:
        return text

    # 自动二次翻译
    prompt = (
        "请把下面文字完整翻译成自然流畅的中文，"
        "且不要包含任何单词注释、词汇解释，只要正常中文句子：\n"
        f"{text}"
    )
    # 这里沿用你项目中的 call_openrouter
    from gpt_module import call_openrouter  
    translated = call_openrouter(prompt, temperature=0.3)
    return translated.strip()


def generate_ppt_outline(
    task: str,
    text: str,
    image_paths: list,
    language: str = "zh",
    style: str = "正式"
) -> list[dict]:
    """
    生成 PPT 大纲 + 正文 + 幻灯片动画提示
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

    if language == "zh":
        prompt = (
            f"你是一名专业 PPT 设计师，请用【{style_prompt}】风格，只用中文输出。"
            f"请为以下主题生成 6~8 页结构化大纲（每页：标题 + 要点列表），"
            f"不要包含词汇解释或翻译，"
            f"并且每页最后给出一个适合的 PPT 动画效果建议（例如：淡入、擦除、飞入）：\n"
            f"主题：{task}\n"
            f"参考文字（前1000字）：{text[:1000]}"
        )
    else:
        prompt = (
            f"You are a professional PowerPoint designer. Use {style_prompt} style, English only. "
            f"Generate a 6–8 slide outline (each slide: Title + bullet points). "
            f"No word-level translations or explanations, "
            f"and recommend one animation for each slide (e.g., fade, fly-in, wipe):\n"
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
            slides.append({"title": m.group(1).strip(), "bullets": [], "content": "", "animation": None})
        elif slides and re.match(r"^(?:[-\*•]|\d+[\.、])\s+", line):
            point = re.sub(r"^(?:[-\*•]|\d+[\.、])\s*", "", line).strip()
            slides[-1]["bullets"].append(point)
        elif ("动画" in line or "animation" in line) and slides:
            slides[-1]["animation"] = line.strip()

    # 二次展开
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
                 f"No word explanations or translations:\n{pts}"
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
            buf = {"title": s["title"], "content": enriched, "animation": s.get("animation")}

    if buf["content"]:
        merged.append(buf)
    return merged