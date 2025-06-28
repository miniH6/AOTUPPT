from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def fit_font_size(text: str, base_size: int = 20) -> Pt:
    ln = len(text)
    if ln < 300:
        return Pt(base_size)
    elif ln < 500:
        return Pt(base_size - 2)
    elif ln < 700:
        return Pt(base_size - 4)
    else:
        return Pt(base_size - 6)

def auto_linebreak(text: str, interval: int = 60) -> str:
    return "\n".join([text[i:i+interval] for i in range(0, len(text), interval)])

def chunk_text(text: str, max_chars: int = 400) -> list[str]:
    paras = [p for p in text.split("\n") if p.strip()]
    pages = []
    buf = ""
    for para in paras:
        if len(buf) + len(para) + 1 <= max_chars:
            buf = buf + "\n" + para if buf else para
        else:
            if buf:
                pages.append(buf)
            p = para
            while len(p) > max_chars:
                pages.append(p[:max_chars])
                p = p[max_chars:]
            buf = p
    if buf:
        pages.append(buf)
    return pages

def set_font(text_frame, font_name: str, font_size: Pt = Pt(24), bold: bool = False, align_center: bool = False):
    for p in text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER if align_center else PP_ALIGN.LEFT
        for run in p.runs:
            run.font.name = font_name
            run.font.size = font_size
            run.font.bold = bold
            run.font.color.rgb = RGBColor(0, 0, 0)

def create_ppt(
    slides: list[dict],
    image_paths: list[str],
    background: str | None = None,
    title_font: str = "微软雅黑",
    body_font: str = "微软雅黑"
) -> str:
    prs = Presentation()
    w, h = prs.slide_width, prs.slide_height
    MAX_CHARS_PER_SLIDE = 400

    for slide in slides:
        is_image_slide = "image_path" in slide

        if is_image_slide:
            # —— 图片页 + 简要说明
            sl = prs.slides.add_slide(prs.slide_layouts[6])

            # 背景
            if background:
                pic_bg = sl.shapes.add_picture(background, 0, 0, width=w, height=h)
                spTree = sl.shapes._spTree
                sp = pic_bg._element
                spTree.remove(sp)
                spTree.insert(2, sp)

            # 标题
            title_box = sl.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
            title_tf = title_box.text_frame
            title_tf.text = slide["title"]
            set_font(title_tf, title_font, Pt(32), bold=True, align_center=True)

            # 图片
            pic = sl.shapes.add_picture(slide["image_path"], 0, 0)
            pic.left = int((w - pic.width) / 2)
            pic.top = int((h - pic.height) / 2.5)

            # 简述
            desc_box = sl.shapes.add_textbox(Inches(0.8), Inches(5.2), w - Inches(1.6), Inches(2))
            desc_tf = desc_box.text_frame
            trimmed = auto_linebreak(slide["content"].strip()[:200], 50)
            desc_tf.text = trimmed
            set_font(desc_tf, body_font, fit_font_size(trimmed))

            # —— 如果有补充解释，分页补充 —— 
            extended = slide.get("extended", "").strip()
            if extended:
                extended_pages = chunk_text(extended, max_chars=MAX_CHARS_PER_SLIDE)
                for i, txt in enumerate(extended_pages):
                    sl2 = prs.slides.add_slide(prs.slide_layouts[1])
                    if background:
                        pic_bg2 = sl2.shapes.add_picture(background, 0, 0, width=w, height=h)
                        spTree2 = sl2.shapes._spTree
                        sp2 = pic_bg2._element
                        spTree2.remove(sp2)
                        spTree2.insert(2, sp2)

                    # 标题
                    title2_box = sl2.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
                    title2_tf = title2_box.text_frame
                    suffix = f"（补充 {i+1}）" if len(extended_pages) > 1 else "（补充）"
                    title2_tf.text = slide["title"] + suffix
                    set_font(title2_tf, title_font, Pt(32), bold=True)

                    # 内容
                    ph = sl2.placeholders[1]
                    ph.text = auto_linebreak(txt, 60)
                    set_font(ph.text_frame, body_font, fit_font_size(txt))

        else:
            # —— 普通文本页
            content = slide["content"].strip()
            pages = chunk_text(content, max_chars=MAX_CHARS_PER_SLIDE)
            for i, txt in enumerate(pages):
                sl = prs.slides.add_slide(prs.slide_layouts[1])

                if background:
                    pic_bg3 = sl.shapes.add_picture(background, 0, 0, width=w, height=h)
                    spTree3 = sl.shapes._spTree
                    sp3 = pic_bg3._element
                    spTree3.remove(sp3)
                    spTree3.insert(2, sp3)

                # 标题
                title_box = sl.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
                title_tf = title_box.text_frame
                title_tf.text = slide["title"] if i == 0 else slide["title"] + f"（续{ i + 1 }）"
                set_font(title_tf, title_font, Pt(32), bold=True)

                # 内容
                ph = sl.placeholders[1]
                ph.text = auto_linebreak(txt, 60)
                set_font(ph.text_frame, body_font, fit_font_size(txt))

    out = "AutoPPT_AI.pptx"
    prs.save(out)
    return out