# 阶段一 builder：把依赖装到固定目录 /deps
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# 阶段二：换个干净镜像，只把 /deps 搬过来
FROM python:3.12-slim  
WORKDIR /app
ENV PYTHONUNBUFFERED=1
# 告诉 Python 去 /deps 找第三方包
ENV PYTHONPATH=/deps  
# ← 关键：只搬装好的依赖 # 只搬依赖文件，不带 pip 本身、缓存等               
COPY --from=builder /deps /deps      
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]

#最终镜像：依赖文件 + 代码（无 pip 缓存）