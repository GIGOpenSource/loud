"""
响应工具类使用示例
展示如何使用标准化的响应工具类
"""

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .response import (
    ApiResponse, PaginatedResponse, BusinessResponse,
    ResponseCode, ResponseMessage,
    success_response, error_response, paginated_response
)
from .decorators import api_response, paginated_api_response, handle_exceptions
from .exceptions import (
    UserNotFoundException, UserAlreadyExistsException,
    InvalidCredentialsException, RoleNotFoundException
)

User = get_user_model()


# 示例1: 使用ApiResponse类
class UserDetailView(APIView):
    """用户详情视图 - 使用ApiResponse类"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nickname': user.nickname
            }
            
            # 成功响应
            return ApiResponse.success(
                data=user_data,
                message="获取用户信息成功",
                code=ResponseCode.SUCCESS
            )
            
        except User.DoesNotExist:
            # 用户不存在响应
            return BusinessResponse.user_not_found(f"ID: {user_id}")
    
    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # 更新用户信息
            user.nickname = request.data.get('nickname', user.nickname)
            user.save()
            
            # 更新成功响应
            return ApiResponse.updated(
                data={'id': user.id, 'nickname': user.nickname},
                message="用户信息更新成功"
            )
            
        except User.DoesNotExist:
            return BusinessResponse.user_not_found(f"ID: {user_id}")
    
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            
            # 删除成功响应
            return ApiResponse.deleted("用户删除成功")
            
        except User.DoesNotExist:
            return BusinessResponse.user_not_found(f"ID: {user_id}")


# 示例2: 使用分页响应
class UserListView(APIView):
    """用户列表视图 - 使用分页响应"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # 查询用户
        users = User.objects.all().order_by('-date_joined')
        
        # 使用分页响应
        return PaginatedResponse.paginate(
            queryset=users,
            page=page,
            page_size=page_size,
            message="获取用户列表成功",
            code=ResponseCode.SUCCESS
        )


# 示例3: 使用装饰器
@api_view(['POST'])
@permission_classes([AllowAny])
@api_response(
    success_message="用户注册成功",
    error_message="用户注册失败",
    success_code=ResponseCode.CREATED
)
def register_user(request):
    """用户注册 - 使用装饰器"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    # 检查用户是否已存在
    if User.objects.filter(username=username).exists():
        raise UserAlreadyExistsException(f"用户名 {username} 已存在")
    
    # 创建用户
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    # 返回用户数据
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@paginated_api_response(
    page_size=15,
    message="获取角色列表成功"
)
def get_roles(request):
    """获取角色列表 - 使用分页装饰器"""
    from authentication.models import Role
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 15))
    
    roles = Role.objects.filter(is_active=True).order_by('name')
    
    # 返回查询集，装饰器会自动处理分页
    return roles


# 示例4: 使用快捷函数
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """用户登录 - 使用快捷函数"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return error_response(
            message="用户名和密码不能为空",
            code=ResponseCode.VALIDATION_ERROR
        )
    
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            # 登录成功
            return success_response(
                data={
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname
                },
                message="登录成功",
                code=ResponseCode.SUCCESS
            )
        else:
            return BusinessResponse.invalid_credentials()
    except User.DoesNotExist:
        return BusinessResponse.invalid_credentials()


# 示例5: 异常处理
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_exceptions
def get_user_profile(request, username):
    """获取用户资料 - 使用异常处理装饰器"""
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        
        return success_response(
            data={
                'username': user.username,
                'nickname': user.nickname,
                'bio': profile.bio,
                'city': profile.city,
                'country': profile.country
            },
            message="获取用户资料成功"
        )
    except User.DoesNotExist:
        raise UserNotFoundException(f"用户 {username} 不存在")


# 示例6: 自定义业务异常
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role(request):
    """分配角色 - 使用自定义异常"""
    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise UserNotFoundException(f"用户ID {user_id} 不存在")
    
    try:
        from authentication.models import Role
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        raise RoleNotFoundException(f"角色ID {role_id} 不存在")
    
    # 分配角色
    user.roles.add(role)
    
    return success_response(
        data={
            'user_id': user.id,
            'role_id': role.id,
            'message': f"成功为用户 {user.username} 分配角色 {role.name}"
        },
        message="角色分配成功"
    )


# 示例7: 错误响应示例
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def error_examples(request):
    """错误响应示例"""
    error_type = request.GET.get('type', 'validation')
    
    if error_type == 'validation':
        # 数据验证错误
        return ApiResponse.validation_error(
            errors={
                'username': ['用户名不能为空'],
                'email': ['邮箱格式不正确']
            },
            message="数据验证失败"
        )
    
    elif error_type == 'not_found':
        # 资源不存在
        return ApiResponse.not_found("请求的资源不存在")
    
    elif error_type == 'unauthorized':
        # 未授权
        return ApiResponse.unauthorized("请先登录")
    
    elif error_type == 'forbidden':
        # 禁止访问
        return ApiResponse.forbidden("权限不足")
    
    elif error_type == 'internal':
        # 服务器内部错误
        return ApiResponse.internal_error("服务器内部错误")
    
    else:
        return ApiResponse.error("未知错误类型")


# 示例8: 复杂分页响应
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def complex_pagination(request):
    """复杂分页响应示例"""
    from authentication.models import Role
    
    # 获取查询参数
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '')
    
    # 构建查询
    queryset = Role.objects.all()
    if search:
        queryset = queryset.filter(name__icontains=search)
    
    # 使用分页响应
    return paginated_response(
        queryset=queryset,
        page=page,
        page_size=page_size,
        message="获取角色列表成功",
        code=ResponseCode.SUCCESS
    )
