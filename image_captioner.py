import requests, base64, re

def generate_image_caption(image_path, language="zh"):
    b64 = base64.b64encode(open(image_path,"rb").read()).decode()
    if language=="zh":
        prompt = (
            "你是 PPT 演讲者，用中文写一页图解说明：\n"
            "标题：一句话总结\n内容：50~100字\n图片(base64前500):\n"+b64[:500]
        )
    else:
        prompt = (
            "Expert presenter, write title+100 words explanation:\n"
            "Title: …\nContent: …\nImage(base64 first 500):\n"+b64[:500]
        )
    url="https://openrouter.ai/api/v1/chat/completions"
    headers={"Authorization":"Bearer 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","Content-Type":"application/json"}
    data={"model":"mistralai/mistral-7b-instruct","messages":[{"role":"user","content":prompt}],"temperature":0.5}
    resp=requests.post(url,headers=headers,json=data).json()["choices"][0]["message"]["content"].strip()
    if language=="zh":
        m=re.search(r"标题[:：](.*)\n内容[:：](.*)",resp)
        title=m.group(1).strip() if m else "图片说明"
        desc=(m.group(2).strip() if m else resp)[:100]
    else:
        m=re.search(r"Title[:：](.*)\nContent[:：](.*)",resp)
        title=m.group(1).strip() if m else "Image Explanation"
        desc=" ".join((m.group(2).split() if m else resp.split())[:100])
    return {"title":title,"content":desc}