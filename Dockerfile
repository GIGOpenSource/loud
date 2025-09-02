FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update --fix-missing && apt-get install -y \
    gcc \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh

# 暴露端口
EXPOSE 8000

# 使用启动脚本
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
