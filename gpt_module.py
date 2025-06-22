import streamlit as st
import requests
import re
import time
from requests.exceptions import ChunkedEncodingError, ReadTimeout, HTTPError

def call_openrouter(
    prompt: str,
    model: str = "mistralai/mistral-7b-instruct",
    temperature: float = 0.7,
    max_retries: int = 3,
    timeout: float = 60.0
) -> str:
    """
    调用 OpenRouter 接口，返回模型输出的纯文本 content。
    增加超时和重试机制，以应对断流或超时错误。
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
        except (ChunkedEncodingError, ReadTimeout) as e:
            if attempt < max_retries:
                time.sleep(attempt)  # 指数退避可调整
                continue
            raise
        except HTTPError:
            # 让调用方看到原始状态码和消息
            raise

def generate_ppt_outline(
    task: str,
    text: str,
    image_paths: list,
    language: str = "zh"
) -> list[dict]:
    """
    生成 PPT 提纲：
      1) 调用 call_openrouter 获取大纲 raw_outline
      2) 正则匹配标题与要点，构建初步 slides 列表
      3) 再次调用 OpenRouter 将要点展开为段落，并合并短页面
    返回格式：[{ "title": ..., "content": ... }, ...]
    """
    # 1. 构造 prompt
    if language == "zh":
        prompt = (
            "你是一名优秀的 PPT 设计师，只能使用中文输出。"
            "请根据下面主题生成 6~8 页结构化大纲（每页：标题 + 要点列表）：\n"
            f"主题：{task}\n"
            f"参考文字（前1000字）：{text[:1000]}"
        )
    else:
        prompt = (
            "You are a great PowerPoint designer. Output in English only."
            "Based on the topic below, generate a 6–8 slide outline (each slide: Title + bullet points):\n"
            f"Topic: {task}\n"
            f"Reference text (first 1000 chars): {text[:1000]}"
        )

    raw_outline = call_openrouter(prompt)
    slides = []

    # 2. 解析 raw_outline
    for line in raw_outline.splitlines():
        line = line.strip()
        if not line:
            continue
        # 匹配标题
        m = re.match(r"^(?:Slide\s*\d+[:：]|幻灯片\s*\d+[:：]|\d+[\.、])\s*(.+)$", line)
        if m:
            slides.append({"title": m.group(1).strip(), "bullets": [], "content": ""})
        elif slides and re.match(r"^(?:[-\*•]|\d+[\.、])\s+", line):
            point = re.sub(r"^(?:[-\*•]|\d+[\.、])\s*", "", line).strip()
            slides[-1]["bullets"].append(point)

    # 3. 要点展开并合并
    merged = []
    buf = {"title": "", "content": ""}
    char_limit = 300

    for s in slides:
        if not s["bullets"]:
            continue
        pts = "\n".join(s["bullets"])
        exp_prompt = (
            ("请用中文将以下要点展开为一段简洁流畅的幻灯片正文：\n" + pts)
            if language == "zh"
            else ("Please expand the following bullet points into a concise slide paragraph:\n" + pts)
        )
        paragraph = call_openrouter(exp_prompt, temperature=0.6).strip()

        # 若缓冲区剩余空间足够，合并
        if buf["content"] and len(buf["content"]) + len(paragraph) < char_limit:
            buf["content"] += "\n" + paragraph
        else:
            if buf["content"]:
                merged.append(buf)
            buf = {"title": s["title"], "content": paragraph}

    if buf["content"]:
        merged.append(buf)
    return merged