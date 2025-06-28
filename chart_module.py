import pandas as pd
import matplotlib.pyplot as plt
from gpt_module import call_openrouter

def generate_chart_slide_from_csv(csv_path: str, language="zh") -> dict:
    df = pd.read_csv(csv_path)
    fig, ax = plt.subplots(figsize=(6, 4))
    df.plot(ax=ax)
    fig.tight_layout()
    chart_path = "temp_img/plot.png"
    fig.savefig(chart_path)
    plt.close(fig)

    cols = ", ".join(df.columns)
    prompt = (
        f"以下是由列 {cols} 构成的图表，请写一句标题和一句简洁说明总结其主要趋势。"
        if language == "zh" else
        f"Given a chart with columns {cols}, write a one-line title and a concise summary of the main trend."
    )
    desc = call_openrouter(prompt, temperature=0.5)

    return {
        "title": "数据图表",
        "content": desc.strip(),
        "image_path": chart_path,
        "extended": ""
    }