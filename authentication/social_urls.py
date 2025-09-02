"""
社交登录相关的URL配置
包含Telegram等第三方登录的API端点
"""

from django.urls import path, include
from . import social_views

urlpatterns = [
    # Telegram登录相关端点
    path('telegram/auth/', social_views.TelegramAuthView.as_view(), name='telegram_auth'),
    path('telegram/callback/', social_views.TelegramCallbackView.as_view(), name='telegram_callback'),
    
    # 社交账户管理
    path('accounts/connected/', social_views.ConnectedAccountsView.as_view(), name='connected_accounts'),
    path('accounts/disconnect/<str:provider>/', social_views.DisconnectSocialView.as_view(), name='disconnect_social'),
    
    # 社交登录状态检查
    path('check/', social_views.SocialAuthCheckView.as_view(), name='social_auth_check'),
]
