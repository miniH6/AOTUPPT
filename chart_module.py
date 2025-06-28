import matplotlib.pyplot as plt
import pandas as pd
import os
import streamlit as st
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE

from gpt_module import call_openrouter, enforce_chinese

def generate_chart_slide_from_csv(csv_path: str, language: str = "zh") -> dict:
    """
    读取 CSV，自动绘制图表，生成PPT可用的幻灯片
    """

    # 读取
    df = pd.read_csv(csv_path)

    # 画图
    fig, ax = plt.subplots()
    df.plot(kind="bar", ax=ax)
    ax.set_title("数据可视化")
    ax.set_ylabel("数值")
    ax.set_xlabel("类别")
    plt.tight_layout()

    # 保存临时图
    chart_img = "temp_img/chart.png"
    plt.savefig(chart_img)
    plt.close(fig)

    # 使用 AI 生成图表讲述
    summary_prompt = f"""
请根据下述表格数据，用简洁自然的中文总结出图表的主要结论，100字以内，不允许出现“CSV”或“表格”等字眼。
数据：
{df.to_string(index=False)}
"""
    summary = call_openrouter(summary_prompt, temperature=0.4).strip()
    summary = enforce_chinese(summary)

    # 返回PPT结构
    return {
        "title": "数据分析结果",
        "content": summary + "\n\n图表已自动生成。"
    }