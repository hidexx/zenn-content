import os
import datetime
import random
import string

# 1. 記事の設定
today = datetime.date.today()
title = f"【自動生成】Tech News Summary {today}"
slug_raw = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
filename = f"articles/{slug_raw}.md"

# 2. 記事の中身
content = f"""---
title: "{title}"
emoji: "🤖"
type: "tech"
topics: ["python", "automation"]
published: false
---

# 自動生成テスト

これはPythonスクリプトによって **{today}** に自動生成された記事です。
"""

# 3. ファイルを保存
os.makedirs("articles", exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    f.write(content)
