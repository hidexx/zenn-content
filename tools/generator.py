import os
import datetime
import random
import string
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# 1. 準備
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
today = datetime.date.today()
slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug}.md"

# 2. スクレイピング関数（Webページの中身を読む機能）
def fetch_article_content(url):
    try:
        # 5秒待ってダメなら諦める設定
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        # HTMLから文字だけ抜き出す
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # <p>タグ（本文）を中心に取得
        text_parts = [p.get_text() for p in soup.find_all('p')]
        full_text = " ".join(text_parts)
        
        # 長すぎるとAIがパンクするので、先頭2000文字だけ返す
        return full_text[:2000]
    except Exception as e:
        return "（本文の取得に失敗しました。タイトルから推測します）"

# 3. ネタ元取得
rss_url = "https://hnrss.org/best?count=10" 
feed = feedparser.parse(rss_url)

articles_data = ""
# 記事数（7本）
target_entries = feed.entries[:7]

print(f"{len(target_entries)}本の記事の中身を読みに行きます...")

for i, entry in enumerate(target_entries):
    print(f"Reading: {entry.title}...")
    # ここで中身を読みに行く！
    content_text = fetch_article_content(entry.link)
    
    articles_data += f"""
    【記事{i+1}】
    Source Title: {entry.title}
    Source URL: {entry.link}
    Source Content (抜粋): {content_text}
    ----
    """

print("AIが解説記事を執筆中...")

# 4. AIへの指示
system_prompt = """
あなたは日本のエンジニア向け情報キュレーターです。
渡された「海外のテックニュースの本文」を読み、Zenn読者向けに日本語で分かりやすく解説してください。

【重要：URLの扱い】
入力された「Source URL」は、**絶対に改変せず、そのまま出力に含めてください。**

【出力フォーマット】
## [日本語タイトル]
[Source URLをそのまま転記]

**どんなニュース？:**
(記事の中身を元に、何が発表されたのか、何が起きたのかを具体的に3行で)

**エンジニアへの影響:**
(開発者にとってどういうメリット・デメリットがあるか、技術的背景を含めて解説)

---
(これを全記事分繰り返す)
"""

user_prompt = f"""
以下の英語記事を読み込み、日本のエンジニア向けに解説してください。
日付: {today}

{articles_data}
"""

# 5. AI実行
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.2,
    max_tokens=4000, # 記事数が多いので枠を広げる
)
ai_text = response.choices[0].message.content

# 6. 保存
full_content = f"""---
title: "【Hacker News】海外トレンド速報 ({today})"
emoji: "📰"
type: "tech"
topics: ["news", "technology", "hackernews"]
published: false
---

世界中のエンジニアが注目している「Hacker News」の話題記事トップ7を、AIが中身を読んで解説します。

{ai_text}

---
※この記事はAIによって自動生成・要約されています。正確な情報は元記事をご確認ください。
"""

os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"執筆完了！: {filename}")
