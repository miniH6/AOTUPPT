from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

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
        if "image_path" in slide:
            # —— 图片页：图 + 简要说明 —— 
            sl = prs.slides.add_slide(prs.slide_layouts[6])
            if background:
                pic = sl.shapes.add_picture(background, 0, 0, width=w, height=h)
                spTree = sl.shapes._spTree
                sp = pic._element
                spTree.remove(sp)
                spTree.insert(2, sp)

            # 标题
            title_tb = sl.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
            title_tf = title_tb.text_frame
            title_tf.clear()
            title_tf.text = slide["title"]
            set_font(title_tf, title_font, Pt(32), bold=True, align_center=True)

            # 图片
            pic2 = sl.shapes.add_picture(slide["image_path"], 0, 0)
            pic2.left = int((w - pic2.width) / 2)
            pic2.top = int((h - pic2.height) / 2.5)

            # 简要描述
            body_tb = sl.shapes.add_textbox(Inches(0.8), Inches(5.2), w - Inches(1.6), Inches(2))
            body_tf = body_tb.text_frame
            trimmed = auto_linebreak(slide["content"].strip()[:200], 50)
            body_tf.clear()
            body_tf.text = trimmed
            set_font(body_tf, body_font, fit_font_size(trimmed), align_center=False)

            # —— 拓展解释页（可分页） —— 
            extended_text = slide.get("extended", "").strip()
            if extended_text:
                extended_pages = chunk_text(extended_text, max_chars=MAX_CHARS_PER_SLIDE)
                for i, txt in enumerate(extended_pages):
                    sl2 = prs.slides.add_slide(prs.slide_layouts[1])
                    if background:
                        pic = sl2.shapes.add_picture(background, 0, 0, width=w, height=h)
                        sp = pic._element
                        spTree = sl2.shapes._spTree
                        spTree.remove(sp)
                        spTree.insert(2, sp)

                    # 标题
                    tb = sl2.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
                    tf = tb.text_frame
                    tf.text = slide["title"] + ("（补充说明）" if len(extended_pages) == 1 else f"（补充说明 {i+1}）")
                    set_font(tf, title_font, Pt(32), bold=True)

                    # 内容
                    ph = sl2.placeholders[1]
                    ph.text = auto_linebreak(txt, 60)
                    set_font(ph.text_frame, body_font, fit_font_size(txt), align_center=False)

        else:
            # —— 普通内容页 —— 
            content = slide["content"].strip()
            pages = chunk_text(content, max_chars=MAX_CHARS_PER_SLIDE)
            for i, txt in enumerate(pages):
                sl = prs.slides.add_slide(prs.slide_layouts[1])
                if background:
                    pic = sl.shapes.add_picture(background, 0, 0, width=w, height=h)
                    sp = pic._element
                    spTree = sl.shapes._spTree
                    spTree.remove(sp)
                    spTree.insert(2, sp)

                # 标题
                title_tb = sl.shapes.add_textbox(Inches(0.8), Inches(0.3), w - Inches(1.6), Inches(1))
                title_tf = title_tb.text_frame
                title_tf.clear()
                title_tf.text = slide["title"] if i == 0 else slide["title"] + "（续）"
                set_font(title_tf, title_font, Pt(32), bold=True)

                # 内容
                ph = sl.placeholders[1]
                ph.text = auto_linebreak(txt, 60)
                set_font(ph.text_frame, body_font, fit_font_size(txt), align_center=False)

    out = "AutoPPT_AI.pptx"
    prs.save(out)
    return out