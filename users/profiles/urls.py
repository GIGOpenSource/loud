"""
用户资料URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, UserPublicProfileView

# 创建路由器
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet)

urlpatterns = [
    # 资料管理API
    path('', include(router.urls)),
    
    # 公开资料查看
    path('public/<int:user_id>/', UserPublicProfileView.as_view(), name='public-profile'),
]
