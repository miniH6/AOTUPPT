# app.py

import streamlit as st
import os

# —— 业务模块 ——  
from gpt_module import generate_ppt_outline
from image_captioner import generate_image_caption
from ppt_generator import create_ppt

# —— 语音模块（需 pip install SpeechRecognition pyaudio gTTS） ——  
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

# —— Firebase 多人协作（可选，需要放 firebase_key.json） ——  
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

# —— 视觉增强（可选，需 pip install transformers torch torchvision Pillow） ——  
try:
    from vision import vision_caption
    vision_available = True
except ImportError:
    vision_available = False

st.set_page_config(page_title="AutoPPT AI 幻灯片生成器", layout="wide")
st.sidebar.title("🔧 功能导航")
mode = st.sidebar.radio("", [
    "🚀 PPT 生成",
    "🎙️ 语音输入",
    "👥 协作中心",
    "📦 部署指南",
    "🤖 视觉增强"
])

# —— 1. PPT 生成模块 ——  
if mode == "🚀 PPT 生成":
    st.title("🎯 AutoPPT AI 幻灯片生成器")

    # 语言选择
    lang = st.radio("🌐 请选择语言 / Choose Language", ["中文", "English"])
    language = "zh" if lang == "中文" else "en"

    # 字体设置
    title_font = st.selectbox("选择标题字体", ["微软雅黑", "宋体", "黑体", "Arial", "Times New Roman"])
    body_font  = st.selectbox("选择正文字体", ["微软雅黑", "宋体", "黑体", "Arial", "Times New Roman"])

    # 背景图设置
    st.markdown("### 🎨 背景图设置")
    bg_opts = {
        "无背景": None,
        "简洁蓝色": "backgrounds/blue.jpg",
        "科技风": "backgrounds/tech.jpg"
    }
    bg_choice = st.selectbox("选择内置背景", list(bg_opts.keys()))
    uploaded_bg = st.file_uploader("或上传自定义背景图 (jpg/png)", type=["jpg", "png"])
    if uploaded_bg:
        bg_path = os.path.join("temp_img", uploaded_bg.name)
        with open(bg_path, "wb") as f:
            f.write(uploaded_bg.read())
        background = bg_path
    else:
        background = bg_opts[bg_choice]

    # 任务与文件输入
    task     = st.text_input("📝 请输入生成 PPT 的主题与目标", "")
    txt_file = st.file_uploader("📄 上传文字文件 (txt/pdf)", type=["txt", "pdf"])
    imgs     = st.file_uploader("🖼️ 上传图片 (可多选)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    # —— 独立测试提纲按钮 ——  
    if st.button("🔍 测试提纲"):
        # 把上传文本读成字符串
        text_content = ""
        if txt_file:
            raw = txt_file.read()
            try:
                text_content = raw.decode("utf-8")
            except:
                text_content = raw.decode("gbk", errors="ignore")
        demo = generate_ppt_outline(task, text_content, [], language)
        st.json(demo)

    # —— 真正生成 PPT ——  
    if st.button("🚀 生成PPT"):
        if not task:
            st.warning("请输入主题与目标")
        else:
            with st.spinner("✨ 正在生成 PPT，请稍候..."):
                # 读取文字
                text = ""
                if txt_file:
                    raw = txt_file.read()
                    try:
                        text = raw.decode("utf-8")
                    except:
                        text = raw.decode("gbk", errors="ignore")

                # 保存图片文件到临时目录
                paths = []
                for im in imgs:
                    p = os.path.join("temp_img", im.name)
                    with open(p, "wb") as f:
                        f.write(im.read())
                    paths.append(p)

                # 生成 PPT 提纲
                slides = generate_ppt_outline(task, text, paths, language)

                # 调试：打印提纲列表
                st.write("📝 调试：slides =", slides)

                # 每张图生成说明页
                for p in paths:
                    slides.append(generate_image_caption(p, language))

                # 调用 create_ppt 生成最终文件
                out = create_ppt(
                    slides,
                    paths,
                    background=background,
                    title_font=title_font,
                    body_font=body_font
                )

            st.success("✅ PPT 生成成功！")
            with open(out, "rb") as f:
                st.download_button("⬇️ 下载 PPT", f, file_name="AutoPPT_AI.pptx")

# —— 2. 语音输入 & 自动配音 ——  
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
            buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
            st.audio(buf.read(), format="audio/mp3")
        except Exception as e:
            st.error(f"识别/合成出错：{e}")

# —— 3. 多人协作 ——  
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

# —— 4. 部署指南 ——  
elif mode == "📦 部署指南":
    st.title("📦 在线部署指南")
    st.markdown("""
- **Streamlit Cloud**  
  1. 在 GitHub 新建仓库，并 `git push` 代码  
  2. 登录 [Streamlit Cloud](https://streamlit.io/cloud)，关联仓库，点击 Deploy

- **HuggingFace Spaces**  
  1. 在你的 HF 账号下创建 Space，选择 Streamlit 模板  
  2. 上传代码，等待部署完成

- **本地 Docker 部署示例**  
  ```dockerfile
  FROM python:3.10-slim
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
                """)