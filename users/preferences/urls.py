"""
用户偏好URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserPreferenceViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'preferences', UserPreferenceViewSet)

urlpatterns = [
    # 偏好设置管理API
    path('', include(router.urls)),
]
