import os
import datetime
import random
import string
import feedparser
from openai import OpenAI

# 1. 準備
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
today = datetime.date.today()
slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug}.md"

# 2. ネタ元取得（Hacker News Best）
# 少し多め(10件)に取得しておきます
rss_url = "https://hnrss.org/best?count=10" 
feed = feedparser.parse(rss_url)

articles_data = ""
# ここで「7本」に絞ります（[:7] の数字を変えれば5本でも10本でも調整可能）
for i, entry in enumerate(feed.entries[:7]):
    articles_data += f"""
    【記事{i+1}】
    Source Title: {entry.title}
    Source URL: {entry.link}
    ----
    """

print(f"ニュースを{len(feed.entries[:7])}本取得しました。AIが要約中...")

# 3. AIへの指示
system_prompt = """
あなたは日本のエンジニア向け情報キュレーターです。
渡された「海外のテックニュース」を読み、Zenn読者向けに日本語で要約してください。

【重要：URLの扱い】
入力された「Source URL」は、**絶対に改変せず、そのまま出力に含めてください。**

【出力フォーマット】
## [日本語タイトル]
[Source URLをここにそのまま転記]

**概要:**
(3行要約)

**エンジニアへの影響:**
(技術的視点での一言解説)

---
(これを入力された全記事分繰り返すこと)
"""

user_prompt = f"""
以下の英語記事情報を、日本語で紹介してください。
日付: {today}

{articles_data}
"""

# 4. AI実行
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.2,
    # 記事数が増えたので、最大トークン数を少し余裕を持たせておく（自動で伸びますが念のため）
    max_tokens=3000, 
)
ai_text = response.choices[0].message.content

# 5. 保存
full_content = f"""---
title: "【Hacker News】海外トレンド速報 ({today})"
emoji: "📰"
type: "tech"
topics: ["news", "technology", "hackernews"]
published: false
---

世界中のエンジニアが注目している「Hacker News」の話題記事トップ7をAIが要約してお届けします。

{ai_text}

---
※この記事はAIによって自動生成・要約されています。正確な情報は元記事をご確認ください。
"""

os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"執筆完了！: {filename}")
