"""
用户钱包URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserWalletViewSet, WalletTransactionViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'wallets', UserWalletViewSet)
router.register(r'transactions', WalletTransactionViewSet)

urlpatterns = [
    # 钱包管理API
    path('', include(router.urls)),
]
