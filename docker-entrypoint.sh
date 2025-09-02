#!/bin/bash

# 等待数据库启动
echo "等待数据库启动..."
while ! pg_isready -h postgres -p 5432 -U loud_user; do
    sleep 1
done
echo "数据库已启动"

# 等待Redis启动
echo "等待Redis启动..."
while ! redis-cli -h redis ping; do
    sleep 1
done
echo "Redis已启动"

# 运行数据库迁移
echo "运行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 创建超级用户（如果不存在）
echo "检查超级用户..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('超级用户已创建: admin/admin123')
else:
    print('超级用户已存在')
"

# 执行传入的命令
exec "$@"
