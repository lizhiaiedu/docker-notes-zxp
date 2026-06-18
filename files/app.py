from flask import Flask

app = Flask(__name__)

# 一个简单的页面：直接返回一段 HTML
PAGE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Docker Demo</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0;
           display: flex; min-height: 100vh; align-items: center; justify-content: center;
           margin: 0; }
    .card { background: #1e293b; padding: 48px 56px; border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,.4); text-align: center; }
    h1 { margin: 0 0 12px; font-size: 28px; }
    p  { margin: 4px 0; color: #94a3b8; }
    .badge { display: inline-block; margin-top: 16px; padding: 6px 14px;
             background: #2563eb; color: #fff; border-radius: 999px; font-size: 14px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🐳 Hello from Docker!</h1>
    <p>这个页面跑在一个容器里。</p>
    <p>由 Flask 提供服务，用 Dockerfile 打包。</p>
    <span class="badge">容器运行成功</span>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    return PAGE

if __name__ == "__main__":
    # 监听 0.0.0.0 才能让容器外部访问到（不能用 127.0.0.1）
    app.run(host="0.0.0.0", port=5000)
