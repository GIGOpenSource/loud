# 标准化响应工具类使用文档

## 概述

本工具类提供了标准化的API响应格式，包括单个数据返回、分页数据返回、自定义状态码和错误信息管理。通过统一的响应格式，可以确保API的一致性和可维护性。

## 功能特性

- ✅ **统一响应格式** - 所有API响应都遵循相同的结构
- ✅ **自定义状态码** - 支持业务自定义状态码
- ✅ **分页支持** - 内置分页响应处理
- ✅ **异常处理** - 统一的异常处理和错误响应
- ✅ **装饰器支持** - 简化视图代码的装饰器
- ✅ **业务异常** - 针对特定业务场景的异常类

## 响应格式

### 成功响应格式
```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        // 响应数据
    }
}
```

### 错误响应格式
```json
{
    "success": false,
    "code": 4000,
    "message": "错误信息",
    "data": {
        // 错误详情（可选）
    }
}
```

### 分页响应格式
```json
{
    "success": true,
    "code": 2000,
    "message": "获取数据成功",
    "data": [
        // 分页数据
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 10,
        "total_count": 100,
        "page_size": 10,
        "has_next": true,
        "has_previous": false,
        "next_page": 2
    }
}
```

## 状态码定义

### 成功状态码 (2000-2999)
- `2000` - 操作成功
- `2001` - 创建成功
- `2002` - 更新成功
- `2003` - 删除成功

### 客户端错误状态码 (4000-4999)
- `4000` - 请求参数错误
- `4001` - 未授权访问
- `4003` - 禁止访问
- `4004` - 资源不存在
- `4005` - 请求方法不允许
- `4220` - 数据验证失败

### 服务器错误状态码 (5000-5999)
- `5000` - 服务器内部错误
- `5003` - 服务不可用

### 业务错误状态码 (6000-6999)
- `6001` - 用户不存在
- `6002` - 用户已存在
- `6003` - 无效凭据
- `6004` - 令牌过期
- `6005` - 权限不足
- `6006` - 角色不存在
- `6007` - 角色已存在
- `6008` - 用户资料不存在
- `6009` - 用户偏好设置不存在

## 使用方法

### 1. 基本响应类

#### ApiResponse 类
```python
from utils.response import ApiResponse, ResponseCode, ResponseMessage

# 成功响应
return ApiResponse.success(
    data={'user_id': 1, 'username': 'test'},
    message="获取用户信息成功",
    code=ResponseCode.SUCCESS
)

# 创建成功响应
return ApiResponse.created(
    data={'user_id': 1},
    message="用户创建成功"
)

# 更新成功响应
return ApiResponse.updated(
    data={'user_id': 1, 'nickname': '新昵称'},
    message="用户信息更新成功"
)

# 删除成功响应
return ApiResponse.deleted("用户删除成功")

# 错误响应
return ApiResponse.error(
    message="操作失败",
    code=ResponseCode.BAD_REQUEST
)

# 资源不存在
return ApiResponse.not_found("用户不存在")

# 未授权
return ApiResponse.unauthorized("请先登录")

# 禁止访问
return ApiResponse.forbidden("权限不足")

# 数据验证错误
return ApiResponse.validation_error(
    errors={'username': ['用户名不能为空']},
    message="数据验证失败"
)
```

#### PaginatedResponse 类
```python
from utils.response import PaginatedResponse
from .serializers import UserSerializer

# 分页响应
return PaginatedResponse.paginate(
    queryset=User.objects.all(),
    page=1,
    page_size=10,
    message="获取用户列表成功",
    serializer_class=UserSerializer
)
```

#### BusinessResponse 类
```python
from utils.response import BusinessResponse

# 业务特定响应
return BusinessResponse.user_not_found("用户名: test")
return BusinessResponse.user_already_exists("用户名: test")
return BusinessResponse.invalid_credentials()
return BusinessResponse.token_expired()
return BusinessResponse.insufficient_permissions()
return BusinessResponse.role_not_found("管理员")
return BusinessResponse.profile_not_found()
```

### 2. 快捷函数

```python
from utils.response import success_response, error_response, paginated_response

# 成功响应快捷函数
return success_response(
    data={'user_id': 1},
    message="操作成功"
)

# 错误响应快捷函数
return error_response(
    message="操作失败",
    code=ResponseCode.BAD_REQUEST
)

# 分页响应快捷函数
return paginated_response(
    queryset=User.objects.all(),
    page=1,
    page_size=10
)
```

### 3. 装饰器

#### @api_response 装饰器
```python
from utils.decorators import api_response
from utils.response import ResponseCode, ResponseMessage

@api_view(['POST'])
@api_response(
    success_message="用户注册成功",
    error_message="用户注册失败",
    success_code=ResponseCode.CREATED
)
def register_user(request):
    # 视图逻辑
    user_data = {
        'id': user.id,
        'username': user.username
    }
    return user_data  # 装饰器会自动包装成成功响应
```

#### @paginated_api_response 装饰器
```python
from utils.decorators import paginated_api_response
from .serializers import UserSerializer

@api_view(['GET'])
@paginated_api_response(
    page_size=15,
    message="获取用户列表成功",
    serializer_class=UserSerializer
)
def get_users(request):
    # 返回查询集，装饰器会自动处理分页
    return User.objects.all()
```

#### @handle_exceptions 装饰器
```python
from utils.decorators import handle_exceptions
from utils.exceptions import UserNotFoundException

@api_view(['GET'])
@handle_exceptions
def get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return {'user_id': user.id, 'username': user.username}
    except User.DoesNotExist:
        raise UserNotFoundException(f"用户ID {user_id} 不存在")
```

### 4. 自定义异常

```python
from utils.exceptions import (
    BusinessException, UserNotFoundException,
    UserAlreadyExistsException, InvalidCredentialsException
)

# 抛出业务异常
if not user:
    raise UserNotFoundException("用户不存在")

if User.objects.filter(username=username).exists():
    raise UserAlreadyExistsException(f"用户名 {username} 已存在")

if not user.check_password(password):
    raise InvalidCredentialsException()
```

## 在视图中的完整示例

### 示例1: 用户详情视图
```python
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.response import ApiResponse, BusinessResponse
from utils.exceptions import UserNotFoundException

class UserDetailView(APIView):
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
            
            return ApiResponse.success(
                data=user_data,
                message="获取用户信息成功"
            )
            
        except User.DoesNotExist:
            return BusinessResponse.user_not_found(f"ID: {user_id}")
    
    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.nickname = request.data.get('nickname', user.nickname)
            user.save()
            
            return ApiResponse.updated(
                data={'id': user.id, 'nickname': user.nickname},
                message="用户信息更新成功"
            )
            
        except User.DoesNotExist:
            return BusinessResponse.user_not_found(f"ID: {user_id}")
```

### 示例2: 用户列表视图（分页）
```python
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.response import PaginatedResponse
from .serializers import UserSerializer

class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        search = request.GET.get('search', '')
        
        queryset = User.objects.all()
        if search:
            queryset = queryset.filter(username__icontains=search)
        
        return PaginatedResponse.paginate(
            queryset=queryset,
            page=page,
            page_size=page_size,
            message="获取用户列表成功",
            serializer_class=UserSerializer
        )
```

### 示例3: 使用装饰器的简化视图
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from utils.decorators import api_response, handle_exceptions
from utils.exceptions import UserAlreadyExistsException

@api_view(['POST'])
@permission_classes([AllowAny])
@api_response(
    success_message="用户注册成功",
    success_code=ResponseCode.CREATED
)
@handle_exceptions
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if User.objects.filter(username=username).exists():
        raise UserAlreadyExistsException(f"用户名 {username} 已存在")
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }
```

## 配置说明

### 1. 在 settings.py 中配置异常处理器
```python
REST_FRAMEWORK = {
    # ... 其他配置
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',
}
```

### 2. 在 MIDDLEWARE 中添加异常处理中间件（可选）
```python
MIDDLEWARE = [
    # ... 其他中间件
    'utils.exceptions.ExceptionMiddleware',
]
```

## 最佳实践

1. **统一使用响应工具类** - 避免直接返回 Response 对象
2. **合理使用状态码** - 根据业务场景选择合适的自定义状态码
3. **提供有意义的错误信息** - 错误消息应该清晰明确
4. **使用装饰器简化代码** - 对于简单的视图，使用装饰器可以减少重复代码
5. **自定义业务异常** - 为特定的业务场景创建专门的异常类
6. **保持响应格式一致** - 确保所有API都遵循相同的响应格式

## 扩展说明

### 添加新的状态码
在 `ResponseCode` 类中添加新的状态码：
```python
class ResponseCode:
    # 添加新的业务状态码
    CUSTOM_ERROR = 7001
```

### 添加新的响应消息
在 `ResponseMessage` 类中添加新的消息：
```python
class ResponseMessage:
    # 添加新的消息
    CUSTOM_ERROR = "自定义错误信息"
```

### 添加新的业务异常
在 `exceptions.py` 中添加新的异常类：
```python
class CustomBusinessException(BusinessException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ResponseMessage.CUSTOM_ERROR
    default_code = ResponseCode.CUSTOM_ERROR
```

### 添加新的业务响应方法
在 `BusinessResponse` 类中添加新的方法：
```python
class BusinessResponse:
    @staticmethod
    def custom_error(custom_info: str = None) -> Response:
        message = f"自定义错误: {custom_info}" if custom_info else ResponseMessage.CUSTOM_ERROR
        return ApiResponse.error(message, ResponseCode.CUSTOM_ERROR)
```
