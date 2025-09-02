from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.core.validators import RegexValidator
from .models import User, Role, LoginHistory, AuthToken


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    roles = RoleSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'nickname', 'avatar', 'phone',
            'first_name', 'last_name', 'is_active', 'is_verified',
            'date_joined', 'last_login', 'last_login_at', 'roles'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'last_login_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'nickname', 'phone', 'first_name', 'last_name'
        ]
    
    def validate(self, attrs):
        """验证密码确认"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码和确认密码不匹配")
        return attrs
    
    def validate_username(self, value):
        """验证用户名唯一性"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value
    
    def validate_email(self, value):
        """验证邮箱唯一性"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("邮箱已存在")
        return value
    
    def create(self, validated_data):
        """创建用户"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # 记录登录历史
        LoginHistory.objects.create(
            user=user,
            login_method='password',
            is_successful=True
        )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户信息更新序列化器"""
    
    class Meta:
        model = User
        fields = [
            'nickname', 'avatar', 'phone', 'first_name', 'last_name'
        ]


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    remember_me = serializers.BooleanField(default=False, required=False)
    
    def validate(self, attrs):
        """验证登录信息"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                # 记录失败的登录历史
                try:
                    user = User.objects.get(username=username)
                    LoginHistory.objects.create(
                        user=user,
                        login_method='password',
                        is_successful=False,
                        failure_reason='密码错误'
                    )
                except User.DoesNotExist:
                    pass
                raise serializers.ValidationError("用户名或密码错误")
            
            if not user.is_active:
                # 记录失败的登录历史
                LoginHistory.objects.create(
                    user=user,
                    login_method='password',
                    is_successful=False,
                    failure_reason='账户被禁用'
                )
                raise serializers.ValidationError("用户账户已被禁用")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("必须提供用户名和密码")
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """验证密码"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密码和确认密码不匹配")
        return attrs
    
    def validate_old_password(self, value):
        """验证旧密码"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码错误")
        return value


class PasswordResetSerializer(serializers.Serializer):
    """密码重置序列化器"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """验证邮箱是否存在"""
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("该邮箱不存在或用户已被禁用")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """密码重置确认序列化器"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """验证密码"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密码和确认密码不匹配")
        return attrs


class LoginHistorySerializer(serializers.ModelSerializer):
    """登录历史序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'user', 'ip_address', 'user_agent', 'login_method',
            'is_successful', 'failure_reason', 'login_time'
        ]
        read_only_fields = ['id', 'login_time']


class ShortTokenSerializer(serializers.ModelSerializer):
    """32位短Token序列化器"""
    user = UserSerializer(read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = AuthToken
        fields = [
            'id', 'token', 'token_type', 'user', 'device_info',
            'expires_at', 'is_active', 'last_used_at', 'created_at',
            'is_valid'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'is_valid']
    
    def get_is_valid(self, obj):
        """获取token是否有效"""
        return obj.is_valid()
    
    def to_representation(self, instance):
        """自定义输出格式"""
        data = super().to_representation(instance)
        
        # 隐藏完整的token，只显示前8位
        if 'token' in data:
            data['token_preview'] = data['token'][:8] + '***'
            data.pop('token')  # 移除完整token
        
        return data


class TokenCreateSerializer(serializers.Serializer):
    """Token创建序列化器"""
    user_id = serializers.IntegerField()
    token_type = serializers.ChoiceField(
        choices=AuthToken.TOKEN_TYPE_CHOICES,
        default='access'
    )
    device_info = serializers.JSONField(required=False, default=dict)
    expires_hours = serializers.IntegerField(default=1, min_value=1, max_value=24*30)  # 最长30天
    
    def validate_user_id(self, value):
        """验证用户是否存在"""
        try:
            User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在或已被禁用")
    
    def create(self, validated_data):
        """创建token"""
        user = User.objects.get(id=validated_data['user_id'])
        expires_at = timezone.now() + timezone.timedelta(hours=validated_data['expires_hours'])
        
        return AuthToken.objects.create(
            user=user,
            token=AuthToken.generate_token(),
            token_type=validated_data['token_type'],
            device_info=validated_data.get('device_info', {}),
            expires_at=expires_at
        )


class UserCompactSerializer(serializers.ModelSerializer):
    """紧凑的用户序列化器（用于cookie）"""
    display_name = serializers.ReadOnlyField()
    roles_list = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'nickname', 'display_name',
            'is_active', 'is_verified', 'roles_list', 'last_login_at'
        ]
        read_only_fields = ['id', 'display_name', 'roles_list', 'last_login_at']
    
    def get_roles_list(self, obj):
        """获取角色代码列表"""
        return [role.code for role in obj.roles.filter(is_active=True)]


class LoginResponseSerializer(serializers.Serializer):
    """登录响应序列化器"""
    user = UserSerializer()
    tokens = serializers.DictField()
    session_expires = serializers.BooleanField()
    
    class Meta:
        fields = ['user', 'tokens', 'session_expires']
