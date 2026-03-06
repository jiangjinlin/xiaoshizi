from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache


class SecurityHeadersMiddleware(MiddlewareMixin):
    """为所有响应添加基础安全响应头。
    - X-Robots-Tag: noindex, nofollow（降低被搜索引擎抓取）
    - 可按需添加 Cache-Control 等头（这里只做最小改动）
    """
    def process_response(self, request, response):
        try:
            # 反爬虫：不索引不跟随
            response.setdefault('X-Robots-Tag', 'noindex, nofollow')
            # 统一 JSON API 的内容类型嗅探保护（Django 已设置 nosniff，这里冗余容错）
            response.setdefault('X-Content-Type-Options', 'nosniff')
            # 禁止被嵌入 iframe（Django 默认 X-Frame-Options=DENY）
            response.setdefault('X-Frame-Options', 'DENY')
        except Exception:
            pass
        return response


class SessionAuthRequiredMiddleware(MiddlewareMixin):
    """统一会话登录校验中间件
    作用：除白名单外的 /api/ 路径必须已登录 (session 中存在 user_id)。
    未登录：返回 401 JSON （前端拦截器会提示并跳转登录）。
    白名单：登录、注册、健康检查与概览，以及公开考试选择。
    说明：仅处理以 /api/ 开头的接口，不影响静态/媒体/其他路由。
    同时（可选）强制单端登录：检查缓存中的活跃会话标识是否与当前会话一致；不一致则踢下线。
    """
    PUBLIC_PATHS = {
        '/api/login',
        '/api/register',
        '/api/',            # index 带斜杠
        '/api',             # index 不带斜杠（补充）
        '/api/overview',
        '/api/exam-select', # 新增：公开已发布考试列表
    }

    def _single_session_enforce(self, request):
        if not getattr(settings, 'SINGLE_SESSION_ENFORCE', True):
            return None
        try:
            uid = request.session.get('user_id')
            token = request.session.get('session_uid')
        except Exception:
            uid = None
            token = None
        if not uid:
            return None
        try:
            cached = cache.get(f'user_active_session:{uid}')
        except Exception:
            cached = None
        if not token or not cached or token != cached:
            # 会话已失效或被其他端顶替，强制登出
            try:
                request.session.flush()
            except Exception:
                for k in ['user_id', 'session_uid', 'syllabus_province', 'syllabus_major']:
                    try:
                        request.session.pop(k, None)
                    except Exception:
                        pass
            return JsonResponse({'success': False, 'error_msg': '账号已在其他设备登录或会话失效，请重新登录'}, status=401)
        return None

    def process_request(self, request):
        path = request.path.rstrip('/') + ('/' if request.path.endswith('/') else '')  # 标准化末尾斜杠
        if not path.startswith('/api/'):
            return None
        # 白名单直接放行（支持两种形式）
        if path in self.PUBLIC_PATHS or request.path in self.PUBLIC_PATHS:
            return None
        # 已登录放行（在放行前，做单端登录检查）
        if request.session.get('user_id'):
            ss = self._single_session_enforce(request)
            if ss is not None:
                return ss
            return None
        return JsonResponse({'success': False, 'error_msg': '未登录'}, status=401)
