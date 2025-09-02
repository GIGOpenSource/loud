"""
用户模块统一管理后台
导入子模块的管理配置
"""

# 导入子模块的管理配置
from .profiles.admin import *
from .preferences.admin import *
from .wallets.admin import *

# 自定义管理后台配置
from django.contrib import admin

# 重新设置管理后台标题
admin.site.site_header = "Loud 用户管理系统"
admin.site.site_title = "用户管理"
admin.site.index_title = "欢迎使用用户管理系统"