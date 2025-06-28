AutoPPT AI

一个基于大语言模型与多模态视觉的自动化 PPT 生成系统，支持文本、图像、CSV、语音等多模态输入，快速生成结构化高质量演示文稿。

=============================
🚀 项目亮点
=============================

- 文本生成幻灯片
- 图片智能描述并插入
- CSV 自动绘图 + 解说
- 语音输入转文字
- 讲述风格（正式 / 幽默 / 儿童 / 古风 / 新闻）
- PPT 二次编辑
- Firebase 多人协作
- Docker / HuggingFace Spaces 部署

=============================
📂 目录结构
=============================

auto_ppt_ai/
  app.py                 # Streamlit 主程序
  gpt_module.py          # PPT大纲&内容生成
  chart_module.py        # 图表页生成
  ppt_generator.py       # 生成PPT文件
  image_captioner.py     # 图片说明模块
  vision.py              # BLIP图像描述
  requirements.txt       # 依赖文件
  README.md              # 项目说明
  backgrounds/           # 背景图片

=============================
⚙️ 安装依赖
=============================

建议在虚拟环境：

pip install -r requirements.txt

=============================
☁️ 运行
=============================

streamlit run app.py

=============================
🧪 使用示例
=============================

1. 在“PPT生成”中输入主题
2. 上传 txt/pdf 内容
3. 上传图片
4. 上传 CSV (可选)
5. 选择讲述风格
6. 点击生成
7. 预览并下载
8. 若需要二次编辑，点击左侧“PPT二次编辑”，可针对单页重新生成

=============================
🔑 配置密钥
=============================

在 .streamlit/secrets.toml 里填写：

openrouter_key="YOUR_API_KEY"

并可选 firebase_key.json，用于多人协作。

=============================
🐳 Docker 部署
=============================

FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

=============================
🤝 贡献
=============================

欢迎 PR 或合作，联系：
boshihu25@gmail.com

可以贡献：
- 优化多语言
- 丰富讲述风格
- 更多图表可视化样式

=============================
📄 License
=============================

MIT License

Made with ❤️ by AutoPPT AI 团队