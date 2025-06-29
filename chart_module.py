import matplotlib.pyplot as plt
import pandas as pd
import os
import streamlit as st

from gpt_module import call_openrouter, enforce_language

def generate_chart_slide_from_csv(csv_path: str, language: str = "zh") -> dict:
    """
    读取 CSV，自动绘制图表，生成 PPT 幻灯片
    """

    # 尝试自动多编码兼容
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="gbk", errors="ignore")

    # 绘图
    fig, ax = plt.subplots()
    df.plot(kind="bar", ax=ax)
    ax.set_title("数据可视化")
    ax.set_ylabel("数值")
    ax.set_xlabel("类别")
    plt.tight_layout()

    # 保存临时图像
    chart_img = "temp_img/chart.png"
    plt.savefig(chart_img)
    plt.close(fig)

    # 生成图表讲述
    if language == "zh":
        summary_prompt = f"""
请根据下述数据总结图表主要结论，要求自然流畅的中文，不超过100字，禁止出现“CSV”“表格”等字眼，
并且请推荐一个适合 PPT 中的动画效果（例如飞入、放大、擦除）：
数据：
{df.to_string(index=False)}
"""
    else:
        summary_prompt = f"""
Based on the following data, summarize the main conclusions of the chart in fluent English within 100 words,
and recommend a suitable PowerPoint animation (e.g. fade, fly-in, wipe), do not mention "CSV" or "table":
Data:
{df.to_string(index=False)}
"""
    summary = call_openrouter(summary_prompt, temperature=0.4).strip()
    summary = enforce_language(summary, language)

    # 从 GPT 里提取动画
    animation = "无"
    for word in ["飞入", "放大", "擦除", "渐显", "旋转", "fade", "fly-in", "wipe", "zoom", "appear"]:
        if word in summary:
            animation = word
            break

    return {
        "title": "数据分析结果" if language == "zh" else "Data Analysis Result",
        "content": summary + f"\n\n🎬 推荐动画 / Suggested Animation：{animation}",
        "image_path": chart_img,
        "animation": animation
    }