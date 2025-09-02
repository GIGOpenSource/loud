from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # 认证相关
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('check/', views.check_auth, name='check_auth'),

    
    # 32位短Token相关
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # 密码相关
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # 个人登录历史 (仅当前用户)
    path('my-login-history/', views.UserLoginHistoryView.as_view(), name='user_login_history'),
]
