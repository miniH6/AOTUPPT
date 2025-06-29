import matplotlib.pyplot as plt
import pandas as pd
import os
import streamlit as st
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE

from gpt_module import call_openrouter, enforce_language

def generate_chart_slide_from_csv(csv_path: str, language: str = "zh") -> dict:
    """
    读取 CSV，自动绘制图表，生成PPT可用的幻灯片
    """

    # 读取 CSV
    df = pd.read_csv(csv_path)

    # 画图
    fig, ax = plt.subplots()
    df.plot(kind="bar", ax=ax)
    ax.set_title("数据可视化")
    ax.set_ylabel("数值")
    ax.set_xlabel("类别")
    plt.tight_layout()

    # 保存到临时
    chart_img = "temp_img/chart.png"
    plt.savefig(chart_img)
    plt.close(fig)

    # AI讲述
    summary_prompt = f"""
请根据下述表格数据，用简洁自然的中文总结图表主要结论，且不要出现“CSV”“表格”字眼，100字以内：
数据：
{df.to_string(index=False)}
并请推荐适合该图表在 PPT 中使用的动画效果（如：飞入、放大）。
"""
    summary = call_openrouter(summary_prompt, temperature=0.4).strip()
    summary = enforce_chinese(summary)

    # 从 GPT 返回里提取动画
    animation = "无"
    for word in ["飞入", "放大", "擦除", "渐显", "旋转"]:
        if word in summary:
            animation = word
            break

    # 返回结构
    return {
        "title": "数据分析结果",
        "content": summary + f"\n\n🎬 推荐动画：{animation}",
        "image_path": chart_img
    }