import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
def generate_jwt_token(email,role):
    payload = {
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=2),  # Token hết hạn sau 1 ngày
        'iat': datetime.now(timezone.utc),  # Thời điểm phát hành token
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    return token
def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
def get_jwt_token(request):
    print(request.headers)
    token = request.headers.get('Authorization')
    if not token:
        raise AuthenticationFailed('Token không được cung cấp.')
    
    # Kiểm tra xem token có bắt đầu bằng 'Bearer ' không và cắt bỏ phần đó
    if token.startswith('Bearer '):
        token = token[7:]  # Lấy phần sau 'Bearer '
    else:
        raise AuthenticationFailed('Token không hợp lệ.')

    try:
        # Giải mã token và lấy payload
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        email = payload.get('email')  # Lấy email từ payload của token
        if not email:
            raise AuthenticationFailed('Token không chứa email.')
        return email
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token đã hết hạn.')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Token không hợp lệ.')
def check_token_validity(token):
    try:
        # Giải mã token để kiểm tra tính hợp lệ
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return True  # Token hợp lệ
    except jwt.ExpiredSignatureError:
        return False  # Token hết hạn
    except jwt.InvalidTokenError:
        return False  # Token không hợp lệ
