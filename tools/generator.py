import os
import datetime
import random
import string
import feedparser # RSSを取得するライブラリ
from openai import OpenAI

# 1. 準備
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
today = datetime.date.today()
slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug}.md"

# 2. ネタ元（Hacker NewsのRSS）を取得
# ここを "Best" にすることで、本当に話題のネタだけ拾います
rss_url = "https://hnrss.org/best?count=5" 
feed = feedparser.parse(rss_url)

# 記事データを抽出（トップ3つ）
articles_data = ""
for i, entry in enumerate(feed.entries[:3]):
    articles_data += f"""
    【第{i+1}位】
    タイトル: {entry.title}
    URL: {entry.link}
    ----
    """

print("ニュースを取得しました。AIが要約中...")

# 3. AIへの指示（創作ではなく「要約」を指示）
system_prompt = """
あなたは日本のエンジニア向け情報キュレーターです。
渡された「海外のテックニュース（Hacker News）」の情報を読み、
日本のエンジニアが興味を持つように、以下のフォーマットで日本語解説記事を作成してください。

【出力フォーマット】
## 1. [日本語のキャッチーなタイトル]
([元記事リンク])

**概要:**
(この記事が何について書かれているか、3行程度で要約)

**エンジニアへの影響:**
(なぜこの記事が話題なのか、技術的な視点でひとこと解説)

---
(これを3記事分繰り返す)
"""

user_prompt = f"""
以下の英語記事情報を、Zenn読者向けに日本語で紹介してください。
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
    temperature=0.2, # 要約なので創造性は低くする（事実優先）
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

世界中のエンジニアが注目している「Hacker News」の話題記事をAIが要約してお届けします。

{ai_text}

---
※この記事はAIによって自動生成・要約されています。正確な情報は元記事をご確認ください。
"""

os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"執筆完了！: {filename}")
