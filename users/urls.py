"""
用户模块URL配置
重构后的统一路由配置
"""

from django.urls import path, include
from . import views

urlpatterns = [
    # 统一入口和通用接口
    path('dashboard/', views.user_dashboard, name='user-dashboard'),
    path('overview/', views.user_overview, name='user-overview'),
    path('verify/', views.verify_user, name='verify-user'),
    path('module-info/', views.module_info, name='module-info'),
    
    # 子模块路由
    path('', include('users.profiles.urls')),
    path('', include('users.preferences.urls')),
    path('', include('users.wallets.urls')),
]