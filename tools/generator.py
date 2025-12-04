import os
import datetime
import random
import string
from openai import OpenAI

# 1. 準備：GitHubの金庫から鍵を取り出す
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 2. 設定：ファイル名などを決める
today = datetime.date.today()
slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug}.md"

# 3. AIへの指示（プロンプト）
system_prompt = """
あなたはZennで人気のテックライターです。
エンジニア初心者が興味を持つような「Pythonの便利機能」を1つ紹介する記事を書いてください。
構成は「はじめに」「コード例」「解説」「まとめ」としてください。
"""

print("AIが記事を書いています...")

# 4. AIに書かせる
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"今日のテーマ記事を作成してください（日付: {today}）"}
    ],
)
ai_text = response.choices[0].message.content

# 5. Zenn用に整えて保存
full_content = f"""---
title: "【AI執筆】Python便利機能紹介 ({today})"
emoji: "🐍"
type: "tech"
topics: ["python", "ai"]
published: false
---

{ai_text}
"""

os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"執筆完了！: {filename}")
