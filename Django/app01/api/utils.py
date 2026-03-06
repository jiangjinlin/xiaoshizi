import re
from datetime import datetime
from django.utils import timezone
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from rest_framework.response import Response
from ..models import User
from datetime import timedelta
try:
    from ..models import FaceProfile
except Exception:
    FaceProfile = None
try:
    from ..models import GlobalSetting
except Exception:
    GlobalSetting = None

# 新增：免 CSRF 的 Session 认证（适配前端未携带 CSRF Token 的现状）
try:
    from rest_framework.authentication import SessionAuthentication
    class CsrfExemptSessionAuthentication(SessionAuthentication):
        def enforce_csrf(self, request):
            return  # 覆盖为不校验 CSRF
except Exception:
    pass

# 判断题归一化映射
def_true = {'a', 't', 'true', 'yes', 'y', '1', '对', '正确', '是'}
def_false = {'b', 'f', 'false', 'no', 'n', '0', '错', '错误', '否'}

def norm_tf(x):
    s = str(x).strip().lower()
    if s in def_true:
        return 'true'
    if s in def_false:
        return 'false'
    return s


def fmt_dt(dt, fmt='%Y-%m-%d %H:%M:%S'):
    if not dt:
        return None
    try:
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        return dt.strftime(fmt)
    except Exception:
        return str(dt)


def parse_dt_local(s):
    if not s:
        return None
    try:
        if isinstance(s, (int, float)):
            return timezone.make_aware(datetime.fromtimestamp(s), timezone.get_current_timezone())
        s = str(s)
        if s.endswith('Z'):
            dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
            return timezone.localtime(dt)
        dt = datetime.fromisoformat(s)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception:
        return None


def get_operation_template_url(q, request):
    # 1) 从题干提取 http(s)
    try:
        m = re.search(r'https?://[^\s)\]}]+', str(q.content or ''))
        if m:
            return m.group(0)
    except Exception:
        pass
    # 2) 静态模板
    candidates = [
        f'template/{q.question_id}.docx',
        f'template/{q.question_id}.xlsx',
        f'template/{q.question_id}.pptx',
    ]
    for rel in candidates:
        try:
            if finders.find(rel):
                return request.build_absolute_uri(static(rel))
        except Exception:
            continue
    return None


def require_login(request, roles=None):
    uid = request.session.get('user_id')
    if not uid:
        return None, Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return None, Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    _auto_housekeeping(user)
    if roles and user.role not in roles:
        return None, Response({'success': False, 'error_msg': '权限不足'}, status=403)
    return user, None

# 自动降级过期 VIP 并删除过期人脸
FACE_RECENT_SESSION_KEY = 'face_signin_at'

def _auto_housekeeping(user):
    changed = False
    now = timezone.now()
    # VIP 到期自动降级
    if getattr(user, 'role', '') == 'VIP':
        exp = getattr(user, 'vip_expires_at', None)
        if exp and now > exp:
            user.role = '学生'
            user.vip_expires_at = None
            changed = True
    # 人脸过期删除
    if FaceProfile is not None:
        try:
            fp = FaceProfile.objects.filter(user=user).first()
            if fp and getattr(fp, 'expires_at', None) and now > fp.expires_at:
                fp.delete()
        except Exception:
            pass
    if changed:
        try:
            user.save(update_fields=['role','vip_expires_at'])
        except Exception:
            pass

_def_face_required_cache = {'value': None, 'ts': None}

def is_face_required():
    """全局开关：FACE_REQUIRED == '1' 表示开启需要人脸。结果缓存 30 秒."""
    if GlobalSetting is None:
        return False
    now = timezone.now()
    ts = _def_face_required_cache.get('ts')
    if ts and (now - ts).total_seconds() < 30:
        return bool(_def_face_required_cache.get('value'))
    val = False
    try:
        row = GlobalSetting.objects.filter(key='FACE_REQUIRED').first()
        if row and str(row.value).strip() in {'1','true','yes','on'}:
            val = True
    except Exception:
        val = False
    _def_face_required_cache['value'] = val
    _def_face_required_cache['ts'] = now
    return val

def has_recent_face_signin(request, ttl_minutes: int = None):
    if ttl_minutes is None:
        try:
            ttl_minutes = int(getattr(__import__('django.conf').conf.settings, 'FACE_SIGNIN_TTL_MINUTES', 120))
        except Exception:
            ttl_minutes = 120
    ts = request.session.get(FACE_RECENT_SESSION_KEY)
    if not ts:
        return False
    try:
        dt = datetime.fromtimestamp(int(ts), tz=timezone.get_current_timezone())
        return timezone.now() - dt <= timedelta(minutes=ttl_minutes)
    except Exception:
        return False

# 向后兼容旧命名
_norm_tf = norm_tf


def custom_exception_handler(exc, context):
    """统一 DRF 异常返回格式：{"success": False, "error_msg": "...}
    对限流(Throttled)给出等待秒数提示，其它未处理异常兜底 500。
    """
    from rest_framework.views import exception_handler as drf_handler
    from rest_framework.exceptions import Throttled
    resp = drf_handler(exc, context)
    if resp is not None:
        # 限流特殊提示
        if isinstance(exc, Throttled):
            wait = getattr(exc, 'wait', None)
            msg = f"请求过于频繁，请稍后再试" if not wait else f"请求过于频繁，请 {int(wait)} 秒后再试"
            resp.data = {'success': False, 'error_msg': msg}
            return resp
        # 其它常规 DRF 错误
        if isinstance(resp.data, dict):
            if 'success' in resp.data:
                return resp
            # 提取 detail 或第一个字段
            if 'detail' in resp.data:
                msg = str(resp.data['detail'])
            else:
                # 取第一个非空值
                vals = [v for v in resp.data.values() if v]
                msg = str(vals[0]) if vals else '请求失败'
            resp.data = {'success': False, 'error_msg': msg}
            return resp
        # 其它类型（列表等）
        try:
            msg = str(resp.data)[0:200]
        except Exception:
            msg = '请求失败'
        resp.data = {'success': False, 'error_msg': msg}
        return resp
    # 未被 DRF 捕获：返回通用 500
    return Response({'success': False, 'error_msg': '服务器内部错误'}, status=500)

def month_start(dt=None):
    dt = dt or timezone.now()
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def enforce_face_required(request):
    """若开启全局 FACE_REQUIRED 且会话未在 TTL 内人脸验证，则返回 Response；否则返回 None"""
    try:
        if not is_face_required():
            return None
    except Exception:
        return None
    if has_recent_face_signin(request):
        return None
    return Response({'success': False, 'error_msg': '需先进行人脸验证'}, status=403)
