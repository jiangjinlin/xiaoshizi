from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import User
try:
    from ..models import FaceProfile
except Exception:
    FaceProfile = None
from django.contrib.auth.hashers import check_password, make_password  # 新增
# 新增：登录尝试计数与头像校验
from django.conf import settings
from django.utils import timezone  # 新增：用于时间比较
import os
import time
from io import BytesIO
# 新增：单端登录依赖
from django.core.cache import cache
import secrets
try:
    from PIL import Image
    _PIL_OK = True
except Exception:
    Image = None
    _PIL_OK = False

# 轻量 IP 维度尝试计数（单进程内存，不依赖外部组件）
_LOGIN_TRACK = {}
_LOGIN_MAX_ATTEMPTS = int(os.getenv('LOGIN_MAX_ATTEMPTS', '5'))
_LOGIN_WINDOW_SECONDS = int(os.getenv('LOGIN_WINDOW_SECONDS', '600'))  # 10 分钟窗口
_LOGIN_LOCK_SECONDS = int(os.getenv('LOGIN_LOCK_SECONDS', '600'))      # 封禁 10 分钟


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # 取第一个非空 IP
        parts = [p.strip() for p in xff.split(',') if p.strip()]
        if parts:
            return parts[0]
    return request.META.get('REMOTE_ADDR') or '0.0.0.0'


def _is_locked(ip: str, request) -> tuple[bool, int]:
    now = int(time.time())
    # 会话级锁
    ses_lock = int(request.session.get('login_lock_until') or 0)
    if ses_lock > now:
        return True, max(0, ses_lock - now)
    # IP 级锁
    rec = _LOGIN_TRACK.get(ip)
    if rec and int(rec.get('lock_until', 0)) > now:
        return True, int(rec['lock_until']) - now
    return False, 0


def _record_failure(ip: str, request):
    now = int(time.time())
    # 会话计数
    cnt = int(request.session.get('login_fail_count') or 0) + 1
    request.session['login_fail_count'] = cnt
    # 连续过多失败，触发会话级短暂锁定
    if cnt >= _LOGIN_MAX_ATTEMPTS:
        request.session['login_lock_until'] = now + _LOGIN_LOCK_SECONDS
        # 重置计数，避免累加过大
        request.session['login_fail_count'] = 0

    # IP 计数
    rec = _LOGIN_TRACK.get(ip) or {'count': 0, 'first': now, 'lock_until': 0}
    # 窗口外重置
    if now - int(rec.get('first', now)) > _LOGIN_WINDOW_SECONDS:
        rec = {'count': 0, 'first': now, 'lock_until': 0}
    rec['count'] = int(rec.get('count', 0)) + 1
    # 触发 IP 锁
    if rec['count'] >= _LOGIN_MAX_ATTEMPTS:
        rec['lock_until'] = now + _LOGIN_LOCK_SECONDS
        # 重设窗口起点与计数
        rec['first'] = now
        rec['count'] = 0
    _LOGIN_TRACK[ip] = rec


def _reset_login_track(ip: str, request):
    # 成功登录后清理计数与锁
    request.session.pop('login_fail_count', None)
    request.session.pop('login_lock_until', None)
    rec = _LOGIN_TRACK.get(ip)
    if rec:
        rec['count'] = 0
        rec['lock_until'] = 0
        rec['first'] = int(time.time())
        _LOGIN_TRACK[ip] = rec


# 新增：生成/保存单端登录会话标识
def _bind_active_session(user_id: int, request):
    # 生成新的随机会话标识，绑定到当前会话并写入缓存
    token = secrets.token_urlsafe(18)
    request.session['session_uid'] = token
    # 使用缓存映射 user -> token。注意：多进程/多机需要共享缓存（如 Redis）
    cache.set(f"user_active_session:{user_id}", token, timeout=getattr(settings, 'SESSION_COOKIE_AGE', 1209600))
    return token


@api_view(["POST"])  # 登录
def api_login(request):
    # 频率防护：会话/IP 短暂锁
    ip = _client_ip(request)
    locked, wait = _is_locked(ip, request)
    if locked:
        return Response({"success": False, "error_msg": f"登录频繁，请 {wait} 秒后再试"}, status=429)

    username = (request.data.get("username") or '').strip()
    password = (request.data.get("password") or '').strip()
    if not username or not password:
        _record_failure(ip, request)
        return Response({"success": False, "error_msg": "用户名和密码不能为空"}, status=400)
    try:
        user = User.objects.get(username=username)
        stored = user.password or ''
        is_hashed = '$' in stored and stored.count('$') >= 2  # 简单判断是否已哈希
        auth_ok = False
        if is_hashed:
            auth_ok = check_password(password, stored)
        else:
            # 旧明文：直接比较
            auth_ok = (stored == password)
            if auth_ok:
                # 升级为哈希
                user.password = make_password(password)
                user.save(update_fields=['password'])
        if auth_ok:
            # 登录成功后旋转会话，避免继承旧会话中的任何状态（如考纲选择）
            try:
                request.session.flush()
            except Exception:
                # 兜底清理关键字段
                for k in ['user_id', 'syllabus_province', 'syllabus_major', 'session_uid']:
                    try:
                        request.session.pop(k, None)
                    except Exception:
                        pass
            request.session['user_id'] = user.user_id
            # 绑定为当前用户唯一在线会话（单端登录）
            _bind_active_session(user.user_id, request)
            _reset_login_track(ip, request)
            return Response({
                "success": True,
                "message": "登录成功",
                "role": user.role,
                "user_id": user.user_id
            })
        else:
            _record_failure(ip, request)
            return Response({"success": False, "error_msg": "用户名或密码错误"}, status=400)
    except User.DoesNotExist:
        _record_failure(ip, request)
        return Response({"success": False, "error_msg": "用户不存在"}, status=400)


# 设置 DRF 命名限流作用域
try:
    api_login.throttle_scope = 'login'
except Exception:
    pass


@api_view(["POST"])  # 登出
def api_logout(request):
    # 完全清空会话，确保包括考纲选择在内的所有会话态均被移除
    # 同时撤销单端登录映射（若匹配当前 token）
    try:
        user_id = request.session.get('user_id')
        token = request.session.get('session_uid')
    except Exception:
        user_id = None
        token = None
    try:
        if user_id and token:
            key = f"user_active_session:{user_id}"
            cur = cache.get(key)
            if cur and cur == token:
                cache.delete(key)
    except Exception:
        pass
    try:
        request.session.flush()
    except Exception:
        # 兜底删除关键字段
        for k in ['user_id', 'syllabus_province', 'syllabus_major', 'session_uid']:
            try:
                request.session.pop(k, None)
            except Exception:
                pass
    return Response({"success": True, "message": "退出成功"})


@api_view(["GET"])  # 个人资料
def api_profile_info(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    def avatar_abs_url(u):
        try:
            if u.avatar and hasattr(u.avatar, 'url'):
                return request.build_absolute_uri(u.avatar.url)
        except Exception:
            return None
        return None

    vip_exp = getattr(user, 'vip_expires_at', None)
    face_exp = None
    face_expired = False
    if FaceProfile is not None:
        try:
            fp = FaceProfile.objects.filter(user=user).first()
            if fp:
                face_exp = fp.expires_at
                if face_exp and face_exp < timezone.now():
                    face_expired = True
        except Exception:
            pass
    def _fmt(x):
        from django.utils import timezone as _tz
        try:
            if x and _tz.is_aware(x):
                x = _tz.localtime(x)
            return x.strftime('%Y-%m-%d %H:%M:%S') if x else None
        except Exception:
            return None

    data = {
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role,
        'nickname': user.nickname or '',
        'email': user.email or '',
        'phone': user.phone or '',
        'class_name': user.classroom or '',
        'student_no': user.student_no or '',
        'dept': user.department or '',
        'avatar_url': avatar_abs_url(user),
        'vip_expires_at': _fmt(vip_exp),
        'face_expires_at': _fmt(face_exp),
        'face_expired': face_expired,
    }
    return Response({'success': True, 'profile': data})


@api_view(["POST"])  # 保存资料
def api_profile_save(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    nickname = (request.data.get('nickname') or '').strip()
    email = (request.data.get('email') or '').strip()
    phone = (request.data.get('phone') or '').strip()
    dept = (request.data.get('dept') or '').strip()
    class_name = (request.data.get('class_name') or '').strip()

    if nickname is not None:
        user.nickname = nickname
    if email is not None:
        user.email = email
    if phone is not None:
        user.phone = phone
    if user.role == '老师' and dept:
        user.department = dept
    if user.role == '学生' and class_name:
        user.classroom = class_name
    if user.role == '学生':
        try:
            user.student_no = user.username
        except Exception:
            pass
    user.save()
    return Response({'success': True, 'message': '保存成功'})


@api_view(["POST"])  # 上传头像（含类型/大小校验与图片验证）
def api_profile_avatar(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    f = request.FILES.get('avatar') or request.FILES.get('file')
    if not f:
        return Response({'success': False, 'error_msg': '未选择文件'}, status=400)

    # 大小限制
    try:
        max_bytes = int(getattr(settings, 'AVATAR_MAX_BYTES', 2 * 1024 * 1024))
    except Exception:
        max_bytes = 2 * 1024 * 1024
    size = getattr(f, 'size', None)
    if size is not None and size > max_bytes:
        return Response({'success': False, 'error_msg': '文件过大，限制为 2MB'}, status=400)

    # 类型/扩展名检查
    allowed_ct = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    ct = (getattr(f, 'content_type', '') or '').lower()
    if ct and ct not in allowed_ct:
        return Response({'success': False, 'error_msg': '不支持的图片类型'}, status=400)

    # 读取并用 Pillow 验证
    try:
        raw = f.read()
        if max_bytes and len(raw) > max_bytes:
            return Response({'success': False, 'error_msg': '文件过大，限制为 2MB'}, status=400)
        if _PIL_OK:
            with Image.open(BytesIO(raw)) as im:
                im.verify()  # 仅验证，不解码全图
        # 将指针复位不再依赖，直接用内存内容回写到 File
        from django.core.files.base import ContentFile
        user.avatar = ContentFile(raw, name=getattr(f, 'name', 'avatar.jpg'))
        user.save()
        url = None
        try:
            if user.avatar and hasattr(user.avatar, 'url'):
                url = request.build_absolute_uri(user.avatar.url)
        except Exception:
            url = None
        return Response({'success': True, 'avatar_url': url})
    except Exception:
        return Response({'success': False, 'error_msg': '图片校验失败或文件损坏'}, status=400)


@api_view(["POST"])  # 绑定占位
def api_profile_bind(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    return Response({'success': True, 'message': '绑定操作已受理（占位）'})
