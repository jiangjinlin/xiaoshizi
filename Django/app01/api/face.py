import os
import io
import base64
import uuid
from datetime import datetime, timedelta
from typing import Tuple

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import User, FaceProfile, ExamSignIn, Exam
try:
    from ..models import GlobalSetting
except Exception:
    GlobalSetting = None
# 新增: 引入 QuestionReview 用于贡献榜判断
try:
    from ..models import QuestionReview
except Exception:
    QuestionReview = None

from .utils import fmt_dt, month_start  # add month_start import

# 兼容导入项目内置的百度AIP SDK（路径含连字符，不能用点号导入）
import sys as _sys
_sdk_dir = os.path.join(os.path.dirname(__file__), '..', 'aip-python-sdk-baidu-ai-face')
_sdk_dir = os.path.abspath(_sdk_dir)
if os.path.isdir(_sdk_dir) and _sdk_dir not in _sys.path:
    _sys.path.insert(0, _sdk_dir)
try:
    from aip import AipFace  # type: ignore
except Exception:
    AipFace = None  # type: ignore

# PIL 用于本地图片哈希
try:
    from PIL import Image, ImageOps
    _PIL_OK = True
except Exception:
    Image = None
    ImageOps = None
    _PIL_OK = False


# --------- 工具 ---------

def _strip_base64_header(s: str) -> str:
    if not s:
        return ''
    s = str(s)
    if ',' in s and s.strip().lower().startswith('data:image'):
        return s.split(',', 1)[1]
    return s


def _image_ahash_from_bytes(raw: bytes):
    if not raw or not _PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(raw)) as im:
            try:
                im = ImageOps.exif_transpose(im)
            except Exception:
                pass
            im = im.convert('L')
            w, h = im.size
            if w != h:
                side = min(w, h)
                left = (w - side) // 2
                top = (h - side) // 2
                im = im.crop((left, top, left + side, top + side))
            im = im.resize((8, 8))
            pixels = list(im.getdata())  # type: ignore
            avg = sum(pixels) / float(len(pixels))
            bits = ''.join('1' if p >= avg else '0' for p in pixels)
            return bits if len(bits) == 64 else None
    except Exception:
        return None


def _local_image_ahash_from_b64(img_b64: str):
    s = _strip_base64_header(img_b64)
    if not s or not _PIL_OK:
        return None
    try:
        raw = base64.b64decode(s)
        return _image_ahash_from_bytes(raw)
    except Exception:
        return None


def _hamming(a: str, b: str) -> int:
    if not a or not b or len(a) != len(b):
        return 64
    return sum(1 for i, j in zip(a, b) if i != j)


def _hash_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    d = _hamming(a, b)
    return max(0.0, 100.0 * (1.0 - d / 64.0))


def _get_face_client() -> Tuple[object, str | None]:
    conf = getattr(settings, 'BAIDU_FACE', None) or {}
    if not AipFace:
        return None, 'SDK 未安装'
    app_id = conf.get('APP_ID')
    api_key = conf.get('API_KEY')
    secret = conf.get('SECRET_KEY')
    if not app_id or not api_key or not secret:
        return None, '人脸识别未配置'
    try:
        client = AipFace(app_id, api_key, secret)
        client.setConnectionTimeoutInMillis(8000)
        client.setSocketTimeoutInMillis(8000)
        return client, None
    except Exception as e:
        return None, f'初始化失败: {e}'


def _ensure_group(client, group_id: str):
    try:
        r = client.groupAdd(group_id)
        if isinstance(r, dict) and r.get('error_code') in (0, 223101):
            return True
    except Exception:
        pass
    return True


def _cloud_user_id(user: User) -> str:
    """Use a stable ASCII ID for cloud face APIs to avoid non-ASCII username issues."""
    try:
        return f"u{int(user.user_id)}"
    except Exception:
        return f"u{str(getattr(user, 'user_id', '') or '').strip()}"


def _cloud_candidate_ids(user: User) -> list[str]:
    """Keep backward compatibility with existing cloud records keyed by username."""
    vals = []
    try:
        vals.append(_cloud_user_id(user))
    except Exception:
        pass
    try:
        uname = str(getattr(user, 'username', '') or '').strip()
        if uname:
            vals.append(uname)
    except Exception:
        pass
    # keep order and deduplicate
    out = []
    for v in vals:
        if v and v not in out:
            out.append(v)
    return out


def _cloud_upsert_face(user: User, raw: bytes) -> tuple[bool, str]:
    """Write/update one user's face to Baidu cloud using stable ASCII user_id."""
    conf = getattr(settings, 'BAIDU_FACE', {}) or {}
    if not (conf.get('APP_ID') and conf.get('API_KEY') and conf.get('SECRET_KEY')):
        return False, '人脸识别未配置'
    client, err = _get_face_client()
    if err:
        return False, err
    group_id = conf.get('GROUP_ID', 'exam_users')
    _ensure_group(client, group_id)
    cloud_uid = _cloud_user_id(user)
    options = {'user_info': user.username, 'quality_control': 'LOW', 'liveness_control': 'NONE'}
    img_b64 = base64.b64encode(raw).decode('ascii')
    try:
        # Prefer update for existing users; fallback to add for first enrollment.
        resp = client.updateUser(img_b64, 'BASE64', group_id, cloud_uid, options)
        if isinstance(resp, dict) and int(resp.get('error_code') or -1) == 0:
            return True, f'百度入库成功({cloud_uid})'
    except Exception:
        pass
    try:
        resp = client.addUser(img_b64, 'BASE64', group_id, cloud_uid, options)
        if isinstance(resp, dict) and int(resp.get('error_code') or -1) == 0:
            return True, f'百度入库成功({cloud_uid})'
    except Exception:
        pass
    return False, '百度入库失败'


def _media_join(*parts):
    try:
        base = settings.MEDIA_ROOT
    except Exception:
        base = os.path.join(os.path.dirname(__file__), '..', 'media')
    return os.path.abspath(os.path.join(base, *parts))


def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def _build_media_url(request, rel_path: str):
    try:
        return request.build_absolute_uri(settings.MEDIA_URL.rstrip('/') + '/' + rel_path.replace('\\', '/'))
    except Exception:
        return None


def _load_meta(sid: str):
    meta_abs = _media_join('faces_pending', f'{sid}.json')
    if not os.path.exists(meta_abs):
        return None, None
    try:
        import json
        with open(meta_abs, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return meta, meta_abs
    except Exception:
        return None, None


def _max_face_bytes():
    try:
        return int(getattr(settings, 'FACE_IMAGE_MAX_BYTES', 3 * 1024 * 1024))
    except Exception:
        return 3 * 1024 * 1024


def _validate_face_b64(img_b64: str) -> tuple[bool, bytes | None, str | None]:
    """解码并验证 base64 图片，检查大小并用 Pillow 验证格式。"""
    if not img_b64:
        return False, None, '缺少人脸图片（base64）'
    s = _strip_base64_header(img_b64)
    try:
        raw = base64.b64decode(s)
    except Exception:
        return False, None, '图片数据无效'
    max_bytes = _max_face_bytes()
    if len(raw) > max_bytes:
        return False, None, '图片过大，限制为 3MB'
    if _PIL_OK:
        try:
            with Image.open(io.BytesIO(raw)) as im:
                im.verify()
        except Exception:
            return False, None, '图片校验失败或文件损坏'
    return True, raw, None


def _top_contributor_ids(limit: int = 50):
    """计算贡献榜前 N 名用户ID（与 api_review_rank 逻辑一致：score = total + 2*consensus）。
    若 QuestionReview 不可用则返回空集合（阻止学生提交，以免绕过规则）。
    简化：数据量通常较小，直接在内存聚合；如后期量大可改为 SQL 分组+连接。
    """
    if QuestionReview is None:
        return set()
    try:
        from django.db.models import Count
        start = month_start()  # monthly window
        # 所有用户的审查总次数（本月）
        totals = QuestionReview.objects.filter(created_at__gte=start).values('user_id').annotate(total=Count('id'))
        user_ids = [t['user_id'] for t in totals]
        if not user_ids:
            return set()
        # 找出共识组合（达到5条相同建议记录）
        consensus = (QuestionReview.objects
                     .values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                     .annotate(c=Count('id')).filter(c__gte=5, created_at__gte=start))
        cons_set = set()
        for r in consensus:
            cons_set.add((r['question_id'], r['suggested_answer'] or '', r['suggested_kp'] or '', r['suggested_primary'] or '', bool(r['answer_wrong'])))
        # 计算每个用户的共识命中次数
        cons_count_map = {}
        if cons_set:
            for uid in user_ids:
                reviews = QuestionReview.objects.filter(user_id=uid).values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                cnt = 0
                for rv in reviews:
                    key = (rv['question_id'], rv['suggested_answer'] or '', rv['suggested_kp'] or '', rv['suggested_primary'] or '', bool(rv['answer_wrong']))
                    if key in cons_set:
                        cnt += 1
                cons_count_map[uid] = cnt
        # 计算综合得分
        scored = []
        for t in totals:
            uid = t['user_id']
            total = int(t['total'])
            consensus_count = int(cons_count_map.get(uid, 0))
            score = total + 2 * consensus_count
            scored.append((uid, score, total))
        scored.sort(key=lambda x: (-x[1], -x[2]))
        return set(uid for uid, _, _ in scored[:limit])
    except Exception:
        return set()


def _rank_position(user_id: int):
    """返回用户在贡献榜中的名次（1 起），若未上榜则返回 None。"""
    if QuestionReview is None:
        return None
    try:
        from django.db.models import Count
        start = month_start()  # monthly window
        totals = QuestionReview.objects.values('user_id').annotate(total=Count('id')).filter(created_at__gte=start)
        if not totals:
            return None
        # 共识集合
        consensus = (QuestionReview.objects
                     .values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                     .annotate(c=Count('id')).filter(c__gte=5, created_at__gte=start))
        cons_set = set()
        for r in consensus:
            cons_set.add((r['question_id'], r['suggested_answer'] or '', r['suggested_kp'] or '', r['suggested_primary'] or '', bool(r['answer_wrong'])))
        cons_count_map = {}
        if cons_set:
            for rec in totals:
                uid = rec['user_id']
                reviews = QuestionReview.objects.filter(user_id=uid).values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                cnt = 0
                for rv in reviews:
                    key = (rv['question_id'], rv['suggested_answer'] or '', rv['suggested_kp'] or '', rv['suggested_primary'] or '', bool(rv['answer_wrong']))
                    if key in cons_set:
                        cnt += 1
                cons_count_map[uid] = cnt
        scored = []
        for rec in totals:
            uid = rec['user_id']
            total = int(rec['total'])
            consensus_count = int(cons_count_map.get(uid, 0))
            score = total + 2 * consensus_count
            scored.append((uid, score, total))
        scored.sort(key=lambda x: (-x[1], -x[2]))
        for idx, (uid, *_rest) in enumerate(scored, start=1):
            if uid == user_id:
                return idx
        return None
    except Exception:
        return None


# --------- API：人脸注册 / 签到 ---------

@api_view(["POST"])  # 人脸注册
def api_face_register(request):
    # 统一要求登录，且仅允许为自身账号绑定；老师/管理员可代为绑定任意 username
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    username = (request.data.get('username') or '').strip()
    image = request.data.get('image') or request.data.get('image_base64') or ''
    ok, raw, err = _validate_face_b64(image)
    if not ok:
        return Response({'success': False, 'error_msg': err}, status=400)

    # 默认使用当前登录用户；若传入 username 必须与本人一致，除非老师/管理员
    bind_username = me.username
    if username:
        if username != me.username and me.role not in ('老师','管理员'):
            return Response({'success': False, 'error_msg': '无权为其他账号绑定人脸'}, status=403)
        bind_username = username

    try:
        user = User.objects.get(username=bind_username)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户名不存在'}, status=404)

    local_ok = False
    local_msg = ''
    try:
        bits = _image_ahash_from_bytes(raw)
        fname = f"u{user.user_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cf = ContentFile(raw, name=fname)
        fp, _ = FaceProfile.objects.get_or_create(user=user)
        fp.image = cf
        fp.vector = (bits or '')[:64]
        # 默认设置有效期 30 天（首次或覆盖）
        try:
            fp.expires_at = timezone.now() + timedelta(days=30)
        except Exception:
            pass
        fp.save()
        local_ok = True
        local_msg = '本地入库成功'
    except Exception:
        local_msg = '本地入库失败'

    cloud_ok = False
    cloud_msg = ''
    conf = getattr(settings, 'BAIDU_FACE', {})
    if conf and conf.get('APP_ID') and conf.get('API_KEY') and conf.get('SECRET_KEY'):
        cloud_ok, cloud_msg = _cloud_upsert_face(user, raw)

    if local_ok or cloud_ok:
        msg = (local_msg or '') + (('；' + cloud_msg) if cloud_msg else '')
        return Response({'success': True, 'message': msg})
    return Response({'success': False, 'error_msg': local_msg or cloud_msg or '人脸入库失败'})

# 为限流打上命名作用域
try:
    api_face_register.throttle_scope = 'face'
except Exception:
    pass


@api_view(["POST"])  # 提交待审核人脸
def api_face_supplement_submit(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    # 权限控制：VIP 可直接提交；学生需在贡献榜前50名；其他角色暂不允许（可按需扩展）
    if user.role == '学生':
        top_ids = _top_contributor_ids(50)
        if user.user_id not in top_ids:
            return Response({'success': False, 'error_msg': '需进入贡献榜前50名方可提交人脸审核'}, status=403)
    elif user.role == 'VIP':
        pass  # 允许，且将直接入库
    else:
        return Response({'success': False, 'error_msg': '当前角色不可提交人脸审核'}, status=403)

    img_b64 = request.data.get('image') or request.data.get('image_base64')
    ok, raw, err = _validate_face_b64(img_b64 or '')
    if not ok:
        return Response({'success': False, 'error_msg': err}, status=400)

    # VIP: 直接入库并生成“已批准”记录，免审核
    if user.role == 'VIP':
        cloud_ok = False
        cloud_msg = ''
        try:
            bits = _image_ahash_from_bytes(raw)
            # 保存到 FaceProfile
            fname = f"u{user.user_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cf = ContentFile(raw, name=fname)
            fp, _ = FaceProfile.objects.get_or_create(user=user)
            fp.image = cf
            fp.vector = (bits or '')[:64]
            fp.expires_at = timezone.now() + timedelta(days=30)
            fp.save()
        except Exception:
            return Response({'success': False, 'error_msg': '更新人脸库失败'}, status=500)

        # 同步云端，避免“补充通过但云端无数据”
        cloud_conf = getattr(settings, 'BAIDU_FACE', {}) or {}
        if cloud_conf.get('APP_ID') and cloud_conf.get('API_KEY') and cloud_conf.get('SECRET_KEY'):
            cloud_ok, cloud_msg = _cloud_upsert_face(user, raw)

        # 生成 faces_pending 目录下的“已批准”记录，便于前端显示与后台查看
        pending_dir = _media_join('faces_pending')
        _ensure_dir(pending_dir)
        stamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        sid = f"{user.user_id}_{stamp}_{uuid.uuid4().hex[:8]}"
        img_rel = f"faces_pending/{sid}.jpg"
        img_abs = _media_join(img_rel)
        meta_rel = f"faces_pending/{sid}.json"
        meta_abs = _media_join(meta_rel)
        try:
            with open(img_abs, 'wb') as wf:
                wf.write(raw)
            import json
            meta = {
                'id': sid,
                'user_id': user.user_id,
                'username': user.username,
                'created_at': fmt_dt(timezone.now()),
                'status': 'approved',
                'image_rel': img_rel,
                'image_url': _build_media_url(request, img_rel),
                'reason': '',
                'approved_at': fmt_dt(timezone.now()),
                'approver': {'user_id': user.user_id, 'username': user.username, 'role': 'VIP', 'auto': True},
            }
            with open(meta_abs, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception:
            # 元数据生成失败不影响绑定结果
            pass
        msg = 'VIP 已直接绑定，无需审核'
        if cloud_msg:
            msg = f'{msg}；{cloud_msg}'
        return Response({'success': True, 'id': sid, 'status': 'approved', 'cloud_ok': cloud_ok, 'message': msg})

    # 非 VIP（学生）：按原逻辑进入待审核
    pending_dir = _media_join('faces_pending')
    _ensure_dir(pending_dir)
    stamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    sid = f"{user.user_id}_{stamp}_{uuid.uuid4().hex[:8]}"
    img_rel = f"faces_pending/{sid}.jpg"
    img_abs = _media_join(img_rel)
    meta_rel = f"faces_pending/{sid}.json"
    meta_abs = _media_join(meta_rel)
    try:
        with open(img_abs, 'wb') as wf:
            wf.write(raw)
        import json
        meta = {
            'id': sid,
            'user_id': user.user_id,
            'username': user.username,
            'created_at': fmt_dt(timezone.now()),
            'status': 'pending',
            'image_rel': img_rel,
            'image_url': _build_media_url(request, img_rel),
            'reason': '',
            'approved_at': None,
            'approver': None,
        }
        with open(meta_abs, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return Response({'success': True, 'id': sid, 'status': 'pending'})
    except Exception:
        return Response({'success': False, 'error_msg': '保存失败'}, status=500)

try:
    api_face_supplement_submit.throttle_scope = 'face'
except Exception:
    pass


@api_view(["GET"])  # 学生查看补充状态
def api_face_supplement_status(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    pending_dir = _media_join('faces_pending')
    items = []
    try:
        for name in os.listdir(pending_dir):
            if not name.endswith('.json'):
                continue
            meta_abs = os.path.join(pending_dir, name)
            try:
                import json
                with open(meta_abs, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                if int(meta.get('user_id')) != int(user.user_id):
                    continue
                if not meta.get('image_url') and meta.get('image_rel'):
                    meta['image_url'] = _build_media_url(request, meta.get('image_rel'))
                items.append(meta)
            except Exception:
                continue
    except Exception:
        items = []
    items = sorted(items, key=lambda m: m.get('created_at') or '', reverse=True)
    return Response({'success': True, 'items': items})

try:
    api_face_supplement_status.throttle_scope = 'face'
except Exception:
    pass


@api_view(["GET"])  # 管理端查看补充
def api_manage_face_supplements(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role not in ('老师', '管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    status_filter = (request.query_params.get('status') or '').strip()
    pending_dir = _media_join('faces_pending')
    rows = []
    try:
        for name in os.listdir(pending_dir):
            if not name.endswith('.json'):
                continue
            try:
                import json
                with open(os.path.join(pending_dir, name), 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                s = str(meta.get('status') or '')
                if status_filter and s != status_filter:
                    continue
                if not meta.get('image_url') and meta.get('image_rel'):
                    meta['image_url'] = _build_media_url(request, meta.get('image_rel'))
                rows.append(meta)
            except Exception:
                continue
    except Exception:
        rows = []
    rows = sorted(rows, key=lambda m: m.get('created_at') or '', reverse=True)
    return Response({'success': True, 'items': rows})

try:
    api_manage_face_supplements.throttle_scope = 'face'
except Exception:
    pass


@api_view(["POST"])  # 审核通过
def api_manage_face_supplement_approve(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role not in ('老师', '管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    sid = request.data.get('id') or request.data.get('sid')
    if not sid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    meta, meta_abs = _load_meta(sid)
    if not meta:
        return Response({'success': False, 'error_msg': '记录不存在'})

    img_rel = meta.get('image_rel')
    img_abs = _media_join(img_rel) if img_rel else None
    if not img_abs or not os.path.exists(img_abs):
        return Response({'success': False, 'error_msg': '图片缺失'})
    try:
        with open(img_abs, 'rb') as f:
            raw = f.read()
        # 大小与图片有效性校验
        if len(raw) > _max_face_bytes():
            return Response({'success': False, 'error_msg': '图片过大，限制为 3MB'})
        if _PIL_OK:
            with Image.open(io.BytesIO(raw)) as im:
                im.verify()
        bits = _image_ahash_from_bytes(raw)
    except Exception:
        return Response({'success': False, 'error_msg': '计算特征失败'})

    try:
        u = User.objects.get(user_id=int(meta.get('user_id')))
    except Exception:
        return Response({'success': False, 'error_msg': '未找到用户'})
    try:
        with open(img_abs, 'rb') as f:
            raw = f.read()
        cf = ContentFile(raw, name=os.path.basename(img_abs))
        fp, _ = FaceProfile.objects.get_or_create(user=u)
        fp.image = cf
        fp.vector = (bits or '')[:64]
        from datetime import timedelta as _td
        fp.expires_at = timezone.now() + _td(days=30)
        fp.save()
    except Exception:
        return Response({'success': False, 'error_msg': '更新人脸库失败'})

    cloud_ok = False
    cloud_msg = ''
    cloud_conf = getattr(settings, 'BAIDU_FACE', {}) or {}
    if cloud_conf.get('APP_ID') and cloud_conf.get('API_KEY') and cloud_conf.get('SECRET_KEY'):
        cloud_ok, cloud_msg = _cloud_upsert_face(u, raw)

    try:
        import json
        meta['status'] = 'approved'
        meta['approved_at'] = fmt_dt(timezone.now())
        meta['approver'] = {'user_id': me.user_id, 'username': me.username}
        with open(meta_abs, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return Response({'success': True, 'cloud_ok': cloud_ok, 'message': cloud_msg or '审核通过'})

try:
    api_manage_face_supplement_approve.throttle_scope = 'face'
except Exception:
    pass


@api_view(["POST"])  # 审核拒绝
def api_manage_face_supplement_reject(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role not in ('老师', '管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    sid = request.data.get('id') or request.data.get('sid')
    reason = (request.data.get('reason') or '').strip()
    if not sid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    meta, meta_abs = _load_meta(sid)
    if not meta:
        return Response({'success': False, 'error_msg': '记录不存在'})
    meta['status'] = 'rejected'
    meta['reason'] = reason
    try:
        import json
        with open(meta_abs, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return Response({'success': True})

try:
    api_manage_face_supplement_reject.throttle_scope = 'face'
except Exception:
    pass


@api_view(["POST"])  # 人脸签到
def api_face_signin(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    exam_id = request.data.get('exam_id') or request.data.get('examId')
    image = request.data.get('image') or request.data.get('image_base64') or ''
    mode = (request.data.get('mode') or '').strip().lower() or 'auto'

    # 通用图片校验
    ok_img, raw, err = _validate_face_b64(image)
    if not ok_img:
        return Response({'success': False, 'error_msg': err or '图片无效'})

    try:
        ttl = int(getattr(settings, 'FACE_SIGNIN_TTL_MINUTES', 120) or 120)
    except Exception:
        ttl = 120

    def _rebuild_vector_if_needed(fp: FaceProfile | None):
        if not _PIL_OK or not fp:
            return fp
        vec = (fp.vector or '').strip()
        need = (not vec) or (len(vec) < 16) or (len(vec) > 128)
        try:
            if need and fp.image and hasattr(fp.image, 'path') and os.path.exists(fp.image.path):
                with open(fp.image.path, 'rb') as f:
                    raw2 = f.read()
                bits2 = _image_ahash_from_bytes(raw2)
                if bits2:
                    fp.vector = bits2[:64]
                    fp.save(update_fields=['vector'])
        except Exception:
            pass
        return fp

    def try_local():
        try:
            local_threshold = float(getattr(settings, 'LOCAL_FACE', {}).get('THRESHOLD', 85.0))
        except Exception:
            local_threshold = 85.0
        fp = None
        try:
            fp = FaceProfile.objects.filter(user=user).first()
        except Exception:
            fp = None
        fp = _rebuild_vector_if_needed(fp)
        if fp and fp.vector:
            probe_bits = _image_ahash_from_bytes(raw)
            sim = _hash_similarity(fp.vector, probe_bits)
            if sim >= local_threshold:
                return True, sim, 'local'
        return False, 0.0, 'local'

    def try_cloud():
        conf = getattr(settings, 'BAIDU_FACE', {})
        if conf and conf.get('APP_ID') and conf.get('API_KEY') and conf.get('SECRET_KEY'):
            client, err = _get_face_client()
            if not err:
                group_id = conf.get('GROUP_ID', 'exam_users')
                candidate_ids = set(_cloud_candidate_ids(user))
                try:
                    threshold = float(conf.get('THRESHOLD', 80.0) or 80.0)
                except Exception:
                    threshold = 80.0
                try:
                    options = {'max_user_num': 5, 'quality_control': 'LOW', 'liveness_control': 'LOW'}
                    img_b64 = base64.b64encode(raw).decode('ascii')
                    resp = client.search(img_b64, 'BASE64', group_id, options)
                    if isinstance(resp, dict) and resp.get('error_code') == 0:
                        user_list = (resp.get('result') or {}).get('user_list') or []
                        match_item = None
                        for it in user_list:
                            if str(it.get('user_id') or '') in candidate_ids:
                                match_item = it
                                break
                        if not match_item and user_list:
                            match_item = user_list[0]
                        if match_item:
                            score_v = float(match_item.get('score') or 0)
                            uid_match = str(match_item.get('user_id') or '')
                            if uid_match in candidate_ids and score_v >= threshold:
                                return True, score_v, 'baidu'
                except Exception:
                    pass
        return False, 0.0, 'baidu'

    # 通用：先本地再云端
    if mode == 'local':
        ok, score, method = try_local()
    elif mode == 'cloud':
        ok, score, method = try_cloud()
    else:
        ok, score, method = try_local()
        if not ok:
            ok, score, method = try_cloud()

    if not exam_id:
        # 通用练习场景：仅设置会话凭证，不写入 ExamSignIn
        if ok:
            request.session['face_signin_at'] = int(timezone.now().timestamp())
            return Response({'success': True, 'score': round(score, 1), 'method': method, 'signed_in': True, 'ttl_minutes': ttl})
        return Response({'success': False, 'error_msg': '识别未通过或未配置'})

    # 以下为考试场景（保留原有逻辑）
    try:
        exam = Exam.objects.get(exam_id=int(exam_id))
    except Exception:
        return Response({'success': False, 'error_msg': '考试不存在'})

    now = timezone.now()
    if not exam.is_published or exam.start_time > now or exam.end_time < now:
        return Response({'success': False, 'error_msg': '不在考试有效时间内'})

    if ok:
        ExamSignIn.objects.create(exam=exam, user=user, success=True, method=method, score=score, reason='')
        request.session['face_signin_at'] = int(timezone.now().timestamp())
        return Response({'success': True, 'score': round(score, 1), 'method': method, 'signed_in': True, 'ttl_minutes': ttl})

    ExamSignIn.objects.create(exam=exam, user=user, success=False, method=method, score=None, reason='识别未通过')
    return Response({'success': False, 'error_msg': '识别未通过或未配置'})

try:
    api_face_signin.throttle_scope = 'face'
except Exception:
    pass


@api_view(["GET"])  # 签到状态
def api_face_status(request):
    uid = request.session.get('user_id')
    try:
        ttl = int(getattr(settings, 'FACE_SIGNIN_TTL_MINUTES', 120) or 120)
    except Exception:
        ttl = 120
    try:
        face_required = False
        if GlobalSetting is not None:
            row = GlobalSetting.objects.filter(key='FACE_REQUIRED').first()
            face_required = bool(row and str(row.value).strip() in {'1','true','yes','on'})
    except Exception:
        face_required = False
    exam_id = request.query_params.get('exam_id') or request.query_params.get('examId')
    if not uid:
        return Response({'success': True, 'signed_in': False, 'ttl_minutes': ttl, 'face_required': face_required})
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': True, 'signed_in': False, 'ttl_minutes': ttl, 'face_required': face_required})

    if not exam_id:
        ts = request.session.get('face_signin_at')
        ok = False
        if ttl > 0 and ts:
            try:
                dt = datetime.fromtimestamp(int(ts), tz=timezone.get_current_timezone())
                ok = timezone.now() - dt <= timedelta(minutes=ttl)
            except Exception:
                ok = False
        return Response({'success': True, 'signed_in': bool(ok), 'ttl_minutes': ttl, 'face_required': face_required})

    try:
        exam = Exam.objects.get(exam_id=int(exam_id))
    except Exception:
        return Response({'success': True, 'signed_in': False, 'ttl_minutes': ttl, 'face_required': face_required})
    since = timezone.now() - timedelta(minutes=ttl)
    ok = ExamSignIn.objects.filter(exam=exam, user=user, success=True, created_at__gte=since).exists()
    return Response({'success': True, 'signed_in': bool(ok), 'ttl_minutes': ttl, 'face_required': face_required})

try:
    api_face_status.throttle_scope = 'face'
except Exception:
    pass


# --------- API：人脸审核资格 ---------

@api_view(["GET"])  # 人脸审核资格查询
def api_face_eligibility(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)

    role = user.role
    eligible = False
    reason = ''
    rank = None
    face_expired = False
    # 检测人脸是否过期
    try:
        fp = FaceProfile.objects.filter(user=user).first()
        if fp and fp.expires_at and fp.expires_at < timezone.now():
            face_expired = True
    except Exception:
        pass

    if role == 'VIP':
        eligible = True
        reason = 'VIP 用户可直接绑定人脸，无需审核'
    elif role == '学生':
        top_ids = _top_contributor_ids(50)
        rank = _rank_position(user.user_id)
        if user.user_id in top_ids:
            eligible = True
            reason = '已进入贡献榜前50名，可提交人脸审核'
        else:
            reason = '需进入贡献榜前50名方可提交人脸审核'
    else:
        reason = '当前角色不可提交人脸审核'

    if face_expired:
        # 人脸过期提示优先于其它提示（但不影响提交资格判断）
        reason = '人脸已过期，请重新提交'
    return Response({'success': True, 'eligible': eligible, 'reason': reason, 'role': role, 'rank': rank, 'face_expired': face_expired})

try:
    api_face_eligibility.throttle_scope = 'face'
except Exception:
    pass


# --------- 额外：人脸档案状态 ---------
@api_view(["GET"])  # 当前用户人脸档案状态
def api_face_profile(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    fp = FaceProfile.objects.filter(user=user).first()
    has_face = False
    expired = False
    expires_at = None
    days_left = None
    if fp and fp.image:
        has_face = True
        expires_at = fp.expires_at
        if expires_at and expires_at < timezone.now():
            expired = True
        if expires_at and not expired:
            delta = expires_at - timezone.now()
            days_left = max(0, int(delta.total_seconds() // 86400))
    def _fmt(dt):
        if not dt:
            return None
        try:
            if timezone.is_aware(dt):
                dt = timezone.localtime(dt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
    return Response({'success': True, 'has_face': has_face, 'expired': expired, 'expires_at': _fmt(expires_at), 'days_left': days_left})

try:
    api_face_profile.throttle_scope = 'face'
except Exception:
    pass

# --------- 全局开关管理（教师/管理员） ---------
@api_view(["GET"])  # 获取全局人脸访问开关
def api_manage_face_setting(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if user.role not in ('老师','管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)
    enabled = False
    if GlobalSetting is not None:
        try:
            row = GlobalSetting.objects.filter(key='FACE_REQUIRED').first()
            enabled = bool(row and str(row.value).strip() in {'1','true','yes','on'})
        except Exception:
            enabled = False
    return Response({'success': True, 'face_required': enabled})

@api_view(["POST"])  # 设置全局人脸访问开关
def api_manage_face_setting_save(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        user = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if user.role not in ('老师','管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)
    val = request.data.get('face_required')
    raw = str(val).strip().lower()
    on = raw in {'1','true','yes','on'}
    if GlobalSetting is None:
        return Response({'success': False, 'error_msg': '后端未启用全局配置模型'}, status=500)
    try:
        row, _ = GlobalSetting.objects.get_or_create(key='FACE_REQUIRED')
        row.value = '1' if on else '0'
        row.save()
    except Exception:
        return Response({'success': False, 'error_msg': '保存失败'}, status=500)
    return Response({'success': True, 'face_required': on})


@api_view(["POST"])  # 管理员重置用户人脸信息（本地+云端）
def api_manage_face_reset(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role != '管理员':
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    target_id = request.data.get('user_id') or request.data.get('id')
    target_name = (request.data.get('username') or '').strip()
    if not target_id and not target_name:
        return Response({'success': False, 'error_msg': '缺少用户标识'}, status=400)

    try:
        if target_id not in (None, ''):
            target = User.objects.get(user_id=int(target_id))
        else:
            target = User.objects.get(username=target_name)
    except Exception:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=404)

    local_deleted = False
    local_msg = ''
    try:
        fp = FaceProfile.objects.filter(user=target).first()
        if fp:
            try:
                if fp.image:
                    fp.image.delete(save=False)
            except Exception:
                pass
            fp.delete()
            local_deleted = True
            local_msg = '本地人脸已删除'
        else:
            local_deleted = True
            local_msg = '本地无可删人脸'
    except Exception:
        local_msg = '本地删除失败'

    cloud_deleted = False
    cloud_msg = ''
    conf = getattr(settings, 'BAIDU_FACE', {})
    if conf and conf.get('APP_ID') and conf.get('API_KEY') and conf.get('SECRET_KEY'):
        client, err_c = _get_face_client()
        if err_c:
            cloud_msg = err_c
        else:
            group_id = conf.get('GROUP_ID', 'exam_users')
            any_deleted = False
            fail_count = 0
            for candidate in _cloud_candidate_ids(target):
                try:
                    resp = client.deleteUser(candidate, group_id)
                    code = int((resp or {}).get('error_code', -1)) if isinstance(resp, dict) else -1
                    if code in (0, 223103, 223105):
                        # 0: success; 223103/223105: user/group not found, treated as idempotent success
                        any_deleted = True
                    else:
                        fail_count += 1
                except Exception:
                    fail_count += 1
            if fail_count == 0:
                cloud_deleted = True
                cloud_msg = '云端人脸已清理'
            elif any_deleted:
                cloud_deleted = True
                cloud_msg = '云端部分清理完成'
            else:
                cloud_msg = '云端删除失败'
    else:
        cloud_deleted = True
        cloud_msg = '云端未配置，已跳过'

    # 删除该用户在 faces_pending 下的历史记录（json + 对应图片）
    pending_deleted = 0
    pending_images_deleted = 0
    try:
        pending_dir = _media_join('faces_pending')
        if os.path.isdir(pending_dir):
            import json
            for name in os.listdir(pending_dir):
                if not name.endswith('.json'):
                    continue
                meta_abs = os.path.join(pending_dir, name)
                try:
                    with open(meta_abs, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    if int(meta.get('user_id') or 0) != int(target.user_id):
                        continue

                    img_rel = meta.get('image_rel')
                    img_abs = _media_join(img_rel) if img_rel else None
                    if img_abs and os.path.exists(img_abs):
                        try:
                            os.remove(img_abs)
                            pending_images_deleted += 1
                        except Exception:
                            pass

                    try:
                        os.remove(meta_abs)
                        pending_deleted += 1
                    except Exception:
                        pass
                except Exception:
                    continue
    except Exception:
        pass

    ok = bool(local_deleted and cloud_deleted)
    return Response({
        'success': ok,
        'user_id': target.user_id,
        'username': target.username,
        'local_deleted': local_deleted,
        'cloud_deleted': cloud_deleted,
        'pending_deleted': pending_deleted,
        'pending_images_deleted': pending_images_deleted,
        'message': f'{local_msg}；{cloud_msg}',
        'error_msg': None if ok else f'{local_msg}；{cloud_msg}',
    }, status=200 if ok else 500)


try:
    api_manage_face_reset.throttle_scope = 'face'
except Exception:
    pass

