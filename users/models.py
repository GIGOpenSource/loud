"""
用户模块统一模型
导入和重新导出子模块的模型
"""

# 用户资料模型
from .profiles.models import UserProfile

# 用户偏好模型
from .preferences.models import UserPreference

# 用户钱包模型
from .wallets.models import UserWallet, WalletTransaction

__all__ = [
    'UserProfile',
    'UserPreference', 
    'UserWallet',
    'WalletTransaction',
]