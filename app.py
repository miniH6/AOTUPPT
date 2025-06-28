import streamlit as st
import os
from gpt_module import call_openrouter

os.makedirs("temp_img", exist_ok=True)

# —— secrets ——  
OPENROUTER_KEY = st.secrets["openrouter_key"]

# —— 业务模块 ——  
from gpt_module import generate_ppt_outline
from image_captioner import generate_image_caption
from ppt_generator import create_ppt
from chart_module import generate_chart_slide_from_csv

# —— 语音模块 ——  
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

# —— firebase（可选） ——  
firebase_enabled = False
if os.path.exists("firebase_key.json"):
    import firebase_admin
    from firebase_admin import credentials, auth, firestore

    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    firebase_enabled = True
else:
    st.sidebar.warning("🔒 firebase_key.json 未找到，多人协作已禁用")

# —— 视觉增强（可选） ——  
try:
    from vision import vision_caption
    vision_available = True
except ImportError:
    vision_available = False

# —— Streamlit 配置 ——  
st.set_page_config(page_title="AutoPPT AI 幻灯片生成器", layout="wide")
st.sidebar.title("🔧 功能导航")
mode = st.sidebar.radio("请选择功能", [
    "🚀 PPT 生成",
    "🎙️ 语音输入",
    "👥 协作中心",
    "📦 部署指南",
    "🤖 视觉增强"
])

# —— PPT 生成 ——  
if mode == "🚀 PPT 生成":
    st.title("🎯 AutoPPT AI 幻灯片生成器")

    lang = st.radio("🌐 请选择语言 / Choose Language", ["中文", "English"])
    language = "zh" if lang == "中文" else "en"

    style = st.selectbox("🗣️ 讲述风格", ["正式", "幽默", "儿童", "新闻播音员", "古风"])

    title_font = st.selectbox("选择标题字体", ["微软雅黑", "宋体", "黑体", "Arial", "Times New Roman"])
    body_font  = st.selectbox("选择正文字体", ["微软雅黑", "宋体", "黑体", "Arial", "Times New Roman"])

    st.markdown("### 🎨 背景图设置")
    bg_opts = {"无背景": None, "简洁蓝色": "backgrounds/blue.jpg", "科技风": "backgrounds/tech.jpg"}
    bg_choice   = st.selectbox("选择内置背景", list(bg_opts.keys()))
    uploaded_bg = st.file_uploader("或上传自定义背景图 (jpg/png)", type=["jpg", "png"])
    if uploaded_bg:
        bg_path = os.path.join("temp_img", uploaded_bg.name)
        with open(bg_path, "wb") as f:
            f.write(uploaded_bg.read())
        background = bg_path
    else:
        background = bg_opts[bg_choice]

    task     = st.text_input("📝 请输入生成 PPT 的主题与目标", "")
    txt_file = st.file_uploader("📄 上传文字文件 (txt/pdf)", type=["txt", "pdf"])
    imgs     = st.file_uploader("🖼️ 上传图片 (可多选)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    csv_file = st.file_uploader("📊 上传 CSV 数据 (可选)", type=["csv"])

    if st.button("🔍 测试提纲"):
        text_content = ""
        if txt_file:
            raw = txt_file.read()
            try:
                text_content = raw.decode("utf-8")
            except:
                text_content = raw.decode("gbk", errors="ignore")
        demo = generate_ppt_outline(task, text_content, [], language, style)
        st.json(demo)

    if st.button("🚀 生成PPT"):
        if not task:
            st.warning("请输入主题与目标")
        else:
            with st.spinner("✨ 正在生成 PPT，请稍候..."):
                text = ""
                if txt_file:
                    raw = txt_file.read()
                    try:
                        text = raw.decode("utf-8")
                    except:
                        text = raw.decode("gbk", errors="ignore")

                paths = []
                for im in imgs:
                    p = os.path.join("temp_img", im.name)
                    with open(p, "wb") as f:
                        f.write(im.read())
                    paths.append(p)

                slides = generate_ppt_outline(task, text, paths, language, style)

                for p in paths:
                    slides.append(generate_image_caption(p, language))

                if csv_file:
                    csv_path = os.path.join("temp_img", csv_file.name)
                    with open(csv_path, "wb") as f:
                        f.write(csv_file.read())
                    slides.append(generate_chart_slide_from_csv(csv_path, language))

                out = create_ppt(
                    slides,
                    paths,
                    background=background,
                    title_font=title_font,
                    body_font=body_font
                )
            st.session_state["slides"] = slides
            st.success("✅ PPT 生成成功！")
            with open(out, "rb") as f:
                st.download_button("⬇️ 点击下载 PPT", f, file_name="AutoPPT_AI.pptx")

# —— 语音输入 ——  
elif mode == "🎙️ 语音输入":
    st.title("🎙️ 语音输入 & 自动配音")
    rec = sr.Recognizer()
    if st.button("开始录音"):
        with sr.Microphone() as mic:
            st.info("🎤 请开始讲话...")
            audio = rec.listen(mic, timeout=5)
        try:
            text = rec.recognize_google(audio, language="zh-CN")
            st.success(f"识别结果：{text}")
            tts = gTTS(text, lang="zh-cn")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf.read(), format="audio/mp3")
        except Exception as e:
            st.error(f"识别/合成出错：{e}")

# —— 多人协作 ——  
elif mode == "👥 协作中心":
    st.title("👥 多人协作")
    if not firebase_enabled:
        st.error("⚠️ 协作功能已禁用 (缺少 firebase_key.json)")
    else:
        action = st.selectbox("操作", ["注册", "登录"])
        email  = st.text_input("邮箱")
        pwd    = st.text_input("密码", type="password")
        if st.button(action):
            try:
                if action == "注册":
                    auth.create_user(email=email, password=pwd)
                    st.success("✅ 注册成功")
                else:
                    docs = db.collection("users").where("email", "==", email).stream()
                    if any(True for _ in docs):
                        st.success("✅ 登录成功")
                    else:
                        st.error("❌ 用户不存在，请先注册")
            except Exception as e:
                st.error(f"Firebase 错误：{e}")

# —— 部署指南 ——  
elif mode == "📦 部署指南":
    st.title("📦 在线部署指南")
    st.markdown("""
- **Streamlit Cloud**  
  1. GitHub 建库并 `git push`  
  2. [Streamlit Cloud](https://streamlit.io/cloud) 关联并部署

- **HuggingFace Spaces**  
  1. 在 HF 创建 Space，选择 Streamlit 模板  
  2. 上传本项目代码

- **本地 Docker**  
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
                """)
# —— 12. 二次编辑 ——  
elif mode == "📝 PPT二次编辑":
    st.title("📝 PPT二次编辑 & 智能再创作")

    # 首先检查 session 是否有 slides
    if "slides" not in st.session_state:
        st.warning("⚠️ 你需要先在“PPT 生成”模块生成一次 PPT 才能进行二次编辑。")
    else:
        slides = st.session_state["slides"]

        st.write("### 当前幻灯片预览")
        for idx, s in enumerate(slides, start=1):
            st.markdown(f"**第 {idx} 页：{s['title']}**")
            st.write(s["content"])
            st.markdown("---")

        edit_idx = st.number_input("选择需要修改的幻灯片页码 (从1开始)", min_value=1, max_value=len(slides), step=1)
        new_prompt = st.text_area("请输入新的提示词 (可指定风格/口气/增加要点等)")
        if st.button("🔁 重新生成选中页"):
            old_slide = slides[edit_idx - 1]
            with st.spinner(f"正在重新生成第 {edit_idx} 页..."):
                # 重新生成该页
                re_prompt = f"""
请根据以下 PPT 页的主题重新生成一段正文，风格尽量参考以下提示：
主题：{old_slide['title']}
原文：
{old_slide['content']}

新的提示：
{new_prompt}
"""
                new_content = call_openrouter(re_prompt, temperature=0.7)
                slides[edit_idx - 1]["content"] = new_content.strip()
                st.success(f"✅ 第 {edit_idx} 页已更新完成！")

        if st.button("⬇️ 重新下载修改后的 PPT"):
            out = create_ppt(
                slides,
                [],   # 二次编辑暂时不重新传图
                background=None,
                title_font="微软雅黑",
                body_font="微软雅黑"
            )
            with open(out, "rb") as f:
                st.download_button("⬇️ 点击下载修改版 PPT", f, file_name="AutoPPT_Revise.pptx")