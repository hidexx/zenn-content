import os
import datetime
import random
import string
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# 1. 準備
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
today = datetime.date.today()
slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug}.md"

# 2. スクレイピング関数（改善版）
def fetch_article_content(url, max_length=2000):
    """
    Webページの本文を取得（エラーハンドリング強化版）
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
        }
        # タイムアウトを15秒に延長
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 不要なタグを削除
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # 記事本文の取得（articleタグ優先）
        article = soup.find('article')
        if article:
            text_parts = [p.get_text(strip=True) for p in article.find_all('p')]
        else:
            text_parts = [p.get_text(strip=True) for p in soup.find_all('p')]
        
        full_text = " ".join(filter(None, text_parts))
        
        # 文字数制限
        return full_text[:max_length] if full_text else "（本文の取得に失敗しました）"
        
    except requests.exceptions.Timeout:
        return "（タイムアウト: サイトの応答が遅いため取得できませんでした）"
    except requests.exceptions.RequestException as e:
        return f"（アクセスエラー: {str(e)[:100]}）"
    except Exception as e:
        return f"（予期しないエラー: {str(e)[:100]}）"

# 3. ネタ元取得
rss_url = "https://hnrss.org/best?count=10" 
print(f"RSSフィードを取得中: {rss_url}")
feed = feedparser.parse(rss_url)

if not feed.entries:
    raise Exception("RSSフィードの取得に失敗しました。ネットワークを確認してください。")

# 記事数を5本に削減（コスト最適化）
target_entries = feed.entries[:5]
print(f"{len(target_entries)}本の記事を処理します...")

articles_data = ""
for i, entry in enumerate(target_entries, 1):
    print(f"[{i}/{len(target_entries)}] Reading: {entry.title[:60]}...")
    content_text = fetch_article_content(entry.link, max_length=1500)
    
    articles_data += f"""
【記事{i}】
Source Title: {entry.title}
Source URL: {entry.link}
Source Content (抜粋): {content_text}
----
"""
    # レート制限対策: 1秒待機
    time.sleep(1)

print("AIが解説記事を執筆中...")

# 4. AIへの指示（プロンプト最適化）
system_prompt = """
あなたは日本のエンジニア向け情報キュレーターです。
渡された「海外のテックニュースの本文」を読み、Zenn読者向けに日本語で分かりやすく解説してください。

【重要：URLの扱い】
入力された「Source URL」は、**絶対に改変せず、そのまま出力に含めてください。**

【出力フォーマット】
## [日本語タイトル]
[Source URLをそのまま転記]

**どんなニュース？:**
(記事の中身を元に、何が発表されたのか、何が起きたのかを具体的に2-3行で)

**エンジニアへの影響:**
(開発者にとってどういうメリット・デメリットがあるか、技術的背景を含めて簡潔に解説)

---
(これを全記事分繰り返す)

【注意事項】
- 本文が取得できなかった記事はタイトルとURLのみ掲載
- 推測や憶測は避け、本文に書かれている内容のみを要約
"""

user_prompt = f"""
以下の英語記事を読み込み、日本のエンジニア向けに解説してください。
日付: {today}

{articles_data}
"""

# 5. AI実行（エラーハンドリング追加）
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=3000, # トークン数を削減
    )
    ai_text = response.choices[0].message.content
    
    # コスト情報を出力
    usage = response.usage
    print(f"トークン使用量: {usage.total_tokens} tokens")
    print(f"推定コスト: ${usage.total_tokens * 0.00000015:.6f}")
    
except Exception as e:
    raise Exception(f"OpenAI API呼び出しに失敗しました: {str(e)}")

# 6. 保存
full_content = f"""---
title: "【Hacker News】海外トレンド速報 ({today})"
emoji: "📰"
type: "tech"
topics: ["news", "technology", "hackernews"]
published: false
---

世界中のエンジニアが注目している「Hacker News」の話題記事トップ{len(target_entries)}を、AIが中身を読んで解説します。

{ai_text}

---
※この記事はAIによって自動生成・要約されています。正確な情報は元記事をご確認ください。
"""

os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"✅ 執筆完了！: {filename}")
