from functools import wraps
from django.http import JsonResponse
from django.conf import settings
import jwt

def authenticate_token(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Authentication token required'}, status=401)
        
        try:
            token = token.split(' ')[1]  # Lấy token từ 'Bearer <token>'
            decoded_token = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user = decoded_token  # Lưu thông tin người dùng vào request
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        return func(request, *args, **kwargs)
    return wrapper

def check_role(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if hasattr(request, 'user'):
                user_role = request.user.get('role')
                if user_role not in allowed_roles:
                    return JsonResponse({'error': 'Permission denied'}, status=403)
            else:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            return func(request, *args, **kwargs)
        return wrapper
    return decorator
