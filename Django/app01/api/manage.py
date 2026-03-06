import io
import openpyxl
from django.db.models import Avg
from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import timedelta as _td  # 新增：使用标准 timedelta
from datetime import datetime as _dt    # 新增：用于类型检查

from ..models import User, ExamRecord, ExamQuestion, Question, Exam
try:
    from ..models import FaceProfile, GlobalSetting
except Exception:
    FaceProfile = None
    GlobalSetting = None
# 新增：题目评论管理
from ..models import QuestionComment
from .utils import fmt_dt, parse_dt_local, require_login
# 新增：密码哈希
from django.contrib.auth.hashers import make_password


def _parse_bool(val):
    s = str(val).strip().lower()
    if s in ('true', '1', 'yes', 'y', 'on'):
        return True
    if s in ('false', '0', 'no', 'n', 'off', ''):
        return False
    try:
        return bool(val)
    except Exception:
        return False


@api_view(["GET"])  # 批次列表
def api_manage_batch_list(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    try:
        raw = Question.objects.values_list('batch', flat=True)
        valid = set()
        for b in raw:
            if b is None: continue
            try:
                s = str(b).strip()
                if not s: continue
                if not s.isdigit():
                    continue
                iv = int(s)
                if iv > 0:
                    valid.add(iv)
            except Exception:
                continue
        batches = sorted(valid)
        return Response({'success': True, 'batches': batches})
    except Exception:
        return Response({'success': True, 'batches': []})


@api_view(["GET"])  # 考试列表
def api_manage_exam_list(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    exams = Exam.objects.all().order_by('-start_time')
    out = []
    for e in exams:
        recs = ExamRecord.objects.filter(exam=e)
        count = recs.count()
        try:
            avg = float(recs.aggregate(Avg('score')).get('score__avg') or 0)
            avg = round(avg, 1)
        except Exception:
            avg = 0.0
        out.append({
            'id': e.exam_id,
            'title': e.title,
            'start_time': fmt_dt(e.start_time),
            'end_time': fmt_dt(e.end_time),
            'duration': e.duration,
            'is_published': bool(e.is_published),
            'count': count,
            'avg': avg,
        })
    q_count = Question.objects.count()
    return Response({'success': True, 'exams': out, 'question_count': q_count})


@api_view(["GET"])  # 考试详情
def api_manage_exam_detail(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    exam_id = request.query_params.get('id') or request.query_params.get('exam_id')
    if not exam_id:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        e = Exam.objects.get(exam_id=int(exam_id))
    except Exception:
        return Response({'success': False, 'error_msg': '考试不存在'})
    batches = list(ExamQuestion.objects.filter(exam=e).values_list('batch', flat=True))
    return Response({'success': True, 'exam': {
        'id': e.exam_id,
        'title': e.title,
        'start_time': fmt_dt(e.start_time),
        'end_time': fmt_dt(e.end_time),
        'duration': e.duration,
        'batches': batches
    }})


@api_view(["POST"])  # 考试保存
def api_manage_exam_save(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    eid = request.data.get('id')
    title = (request.data.get('title') or '').strip()
    st = parse_dt_local(request.data.get('start_time'))
    et = parse_dt_local(request.data.get('end_time'))
    try:
        duration_raw = request.data.get('duration')
        duration = int(duration_raw) if duration_raw not in (None, '', []) else 0
    except Exception:
        duration = 0
    batches = request.data.get('batches') or []

    if not title or not st or not et:
        return Response({'success': False, 'error_msg': '必填项不完整'})
    if st >= et:
        return Response({'success': False, 'error_msg': '结束时间必须晚于开始时间'})

    # 自动时长（分钟）
    auto_duration = False
    if duration <= 0:
        try:
            duration = max(1, int((et - st).total_seconds() // 60))
            auto_duration = True
        except Exception:
            duration = 0
    if duration <= 0:
        return Response({'success': False, 'error_msg': '考试时长无效'})

    # 过滤批次：仅保留题库中存在的批次
    try:
        from django.db.models import Value
        all_exist = set(Question.objects.values_list('batch', flat=True))
    except Exception:
        all_exist = set()
    norm_batches = []
    for b in (batches or []):
        try:
            bi = int(b)
            if bi in all_exist:
                norm_batches.append(bi)
        except Exception:
            continue
    norm_batches = sorted(set(norm_batches))
    if not norm_batches:
        return Response({'success': False, 'error_msg': '至少需要选择一个有效的题目批次'})

    # 保存/更新
    if eid:
        try:
            exam = Exam.objects.get(exam_id=int(eid))
        except Exception:
            return Response({'success': False, 'error_msg': '考试不存在'})
        exam.title = title
        exam.start_time = st
        exam.end_time = et
        exam.duration = duration
        exam.save()
        ExamQuestion.objects.filter(exam=exam).delete()
    else:
        exam = Exam.objects.create(title=title, start_time=st, end_time=et, duration=duration, is_published=False)

    # 重建关联
    for b in norm_batches:
        try:
            ExamQuestion.objects.get_or_create(exam=exam, batch=b)
        except Exception:
            pass

    return Response({'success': True, 'id': exam.exam_id, 'duration': duration, 'auto_duration': auto_duration, 'batches': norm_batches})


@api_view(["POST"])  # 删除考试
def api_manage_exam_delete(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    eid = request.data.get('id') or request.data.get('exam_id')
    if not eid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        exam = Exam.objects.get(exam_id=int(eid))
    except Exception:
        return Response({'success': False, 'error_msg': '考试不存在'})
    exam.delete()
    return Response({'success': True})


@api_view(["POST"])  # 发布/取消发布
def api_manage_exam_publish(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    eid = request.data.get('id') or request.data.get('exam_id')
    is_pub = request.data.get('is_published')
    try:
        exam = Exam.objects.get(exam_id=int(eid))
    except Exception:
        return Response({'success': False, 'error_msg': '考试不存在'})
    exam.is_published = _parse_bool(is_pub)
    exam.save()
    return Response({'success': True})


@api_view(["GET"])  # 题库列表
def api_manage_question_list(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qs = Question.objects.all().order_by('question_id')
    # 新增筛选参数：types(逗号分隔)、batch、knowledge(模糊包含)、primary(一级知识点模糊)、keyword(题干模糊)、reviewed
    types_param = request.query_params.get('types') or request.query_params.get('type')
    if types_param:
        tlist = [t.strip() for t in str(types_param).split(',') if t.strip()]
        if tlist:
            qs = qs.filter(question_type__in=tlist)
    batch_param = request.query_params.get('batch')
    if batch_param not in (None, '', 'null'):
        try:
            qs = qs.filter(batch=int(batch_param))
        except Exception:
            pass
    knowledge_param = request.query_params.get('knowledge') or request.query_params.get('kp')
    if knowledge_param:
        qs = qs.filter(knowledge_points__icontains=knowledge_param.strip())
    primary_param = request.query_params.get('primary') or request.query_params.get('primary_knowledge')
    if primary_param:
        qs = qs.filter(primary_knowledge__icontains=primary_param.strip())
    reviewed_param = request.query_params.get('reviewed') or ''
    if reviewed_param.strip():
        rv = reviewed_param.strip().lower()
        if rv in {'1','true','yes','y','reviewed','已审核'}:
            qs = qs.filter(reviewed=True)
        elif rv in {'0','false','no','n','pending','未审核'}:
            qs = qs.filter(reviewed=False)
    keyword = request.query_params.get('keyword') or request.query_params.get('q') or ''
    if keyword.strip():
        qs = qs.filter(content__icontains=keyword.strip())

    out = []
    type_counts = {}
    kp_set = set()
    pk_set = set()
    for q in qs:
        if q.knowledge_points:
            for part in q.knowledge_points.replace('，', ',').split(','):
                p = part.strip()
                if p:
                    kp_set.add(p)
        if q.primary_knowledge:
            pk_set.add(q.primary_knowledge.strip())
        out.append({
            'id': q.question_id,
            'question_type': q.question_type,
            'content': q.content,
            'score': q.score,
            'batch': q.batch,
            'knowledge_points': q.knowledge_points or '',  # 考纲大类
            'primary_knowledge': q.primary_knowledge or '',
            'reviewed': bool(getattr(q, 'reviewed', False)),  # 新增：审核标记
            'big_category': q.knowledge_points or ''  # 别名，便于前端过渡
        })
        type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
    # 附带一个未审核数量，便于界面提示
    try:
        pending_count = Question.objects.filter(reviewed=False).count()
    except Exception:
        pending_count = 0
    return Response({'success': True, 'questions': out, 'question_count': len(out), 'type_counts': type_counts, 'knowledge_points': sorted(list(kp_set)), 'primary_knowledge_options': sorted(list(pk_set)), 'pending_count': pending_count})


@api_view(["GET"])  # 题目详情
def api_manage_question_detail(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qid = request.query_params.get('id')
    if not qid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        q = Question.objects.get(question_id=int(qid))
    except Exception:
        return Response({'success': False, 'error_msg': '题目不存在'})
    return Response({'success': True, 'question': {
        'id': q.question_id,
        'question_type': q.question_type,
        'score': q.score,
        'content': q.content,
        'A_answer': q.A_answer,
        'B_answer': q.B_answer,
        'C_answer': q.C_answer,
        'D_answer': q.D_answer,
        'answer': q.answer,
        'batch': q.batch,
        'analysis': q.analysis or '',
        'knowledge_points': q.knowledge_points or '',
        'primary_knowledge': q.primary_knowledge or '',
        'reviewed': bool(getattr(q, 'reviewed', False)),
    }})


@api_view(["POST"])  # 题目保存
def api_manage_question_save(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qid = request.data.get('id')
    payload = request.data
    fields = ['question_type','score','content','A_answer','B_answer','C_answer','D_answer','answer','batch','analysis','knowledge_points','primary_knowledge']
    data = {f: payload.get(f) for f in fields}
    # 解析分数
    try:
        if data['score'] not in (None, ''):
            data['score'] = int(data['score'])
    except Exception:
        return Response({'success': False, 'error_msg': '分数需要为数字'})
    # 解析批次（允许为空）
    raw_batch = payload.get('batch')
    if raw_batch in (None, '', []):
        data['batch'] = None
    else:
        try:
            data['batch'] = int(raw_batch)
        except Exception:
            return Response({'success': False, 'error_msg': '批次需要为数字或留空'})
    # 规范化可选文本字段：允许为空，存为空串，避免 None 写入非空列
    for key in ['analysis', 'knowledge_points', 'primary_knowledge', 'A_answer', 'B_answer', 'C_answer', 'D_answer']:
        val = payload.get(key)
        if val in (None, [], {}):
            data[key] = '' if key != 'analysis' else ''
        else:
            try:
                data[key] = str(val).strip()
            except Exception:
                data[key] = '' if key != 'analysis' else ''
    # 新增：审核标记
    if 'reviewed' in payload:
        data['reviewed'] = _parse_bool(payload.get('reviewed'))
    # 基础必填项（不再要求 batch）
    if not data['question_type'] or not data['content'] or not data['answer']:
        return Response({'success': False, 'error_msg': '题型/题干/答案为必填'})

    if qid:
        try:
            q = Question.objects.get(question_id=int(qid))
        except Exception:
            return Response({'success': False, 'error_msg': '题目不存在'})
        for k, v in data.items():
            setattr(q, k, v)
        q.save()
        return Response({'success': True, 'id': q.question_id})
    else:
        q = Question.objects.create(**data)
        return Response({'success': True, 'id': q.question_id})


@api_view(["POST"])  # 删除题目
def api_manage_question_delete(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qid = request.data.get('id')
    if not qid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        Question.objects.get(question_id=int(qid)).delete()
        return Response({'success': True})
    except Exception:
        return Response({'success': False, 'error_msg': '题目不存在'})


@api_view(["GET"])  # 导出题库 Excel
def api_manage_question_export(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'questions'
    # 新增列：已审核
    ws.append(['题目ID','题型','分数','批次','题干','A','B','C','D','答案','解析','考纲大类','一级知识点','已审核'])
    for q in Question.objects.all().order_by('question_id'):
        ws.append([q.question_id, q.question_type, q.score, q.batch, q.content, q.A_answer, q.B_answer, q.C_answer, q.D_answer, q.answer, q.analysis or '', q.knowledge_points or '', q.primary_knowledge or '', '是' if getattr(q, 'reviewed', False) else '否'])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="questions.xlsx"'
    return resp


@api_view(["GET"])  # 成绩列表
def api_manage_score_list(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    exam_id = request.query_params.get('exam_id')
    username = (request.query_params.get('username') or '').strip()
    classroom = (request.query_params.get('classroom') or '').strip()
    try:
        page = int(request.query_params.get('page') or 1)
    except Exception:
        page = 1
    try:
        page_size = int(request.query_params.get('page_size') or 10)
    except Exception:
        page_size = 10
    page_size = max(1, min(100, page_size))

    bins = ['60分以下','60-70分','70-80分','80-90分','90分以上']
    counts = [0,0,0,0,0]
    def bucket(p: float) -> int:
        if p < 60: return 0
        if p < 70: return 1
        if p < 80: return 2
        if p < 90: return 3
        return 4

    qs = ExamRecord.objects.all()
    if exam_id:
        try:
            qs = qs.filter(exam__exam_id=int(exam_id))
        except Exception:
            qs = qs.none()
    if username:
        qs = qs.filter(user__username__icontains=username)
    if classroom:
        qs = qs.filter(user__classroom__icontains=classroom)

    total = qs.count()

    exam_ids = list(set(qs.values_list('exam_id', flat=True))) if total else []
    full_score_map = {}
    for eid in exam_ids:
        try:
            e = Exam.objects.get(exam_id=int(eid))
            batch_ids = [eq.batch for eq in ExamQuestion.objects.filter(exam=e)]
            fs = sum(getattr(q, 'score', 1) for q in Question.objects.filter(batch__in=batch_ids)) or 0
            full_score_map[int(eid)] = int(fs)
        except Exception:
            full_score_map[int(eid)] = 0

    for eid, s in qs.values_list('exam_id', 'score'):
        fs = int(full_score_map.get(int(eid), 0) or 0)
        try:
            p = 100.0 * float(s or 0) / fs if fs > 0 else 0.0
        except Exception:
            p = 0.0
        counts[bucket(p)] += 1

    try:
        avg = float(qs.aggregate(Avg('score')).get('score__avg') or 0.0)
    except Exception:
        avg = 0.0

    start = (page - 1) * page_size
    page_qs = qs.select_related('user', 'exam').order_by('-submit_time')[start:start+page_size]

    records = []
    for r in page_qs:
        eid = int(getattr(r.exam, 'exam_id', 0) or 0)
        fs = int(full_score_map.get(eid, 0) or 0)
        records.append({
            'record_id': r.record_id,
            'username': getattr(r.user, 'username', None),
            'classroom': getattr(r.user, 'classroom', None),
            'exam_title': getattr(r.exam, 'title', None),
            'score': r.score,
            'full_score': fs,
            'start_time': fmt_dt(getattr(r, 'start_time', None)),
            'end_time': fmt_dt(getattr(r, 'end_time', None)),
            'submit_time': fmt_dt(r.submit_time),
        })

    exams = [{'id': e.exam_id, 'title': e.title} for e in Exam.objects.filter(is_published=True).order_by('-start_time')]

    return Response({'success': True, 'score_bins': bins, 'score_counts': counts, 'avg': round(avg,1), 'total': total, 'records': records, 'exams': exams})


@api_view(["POST"])  # 删除成绩
def api_manage_score_delete(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    rid = request.data.get('id') or request.data.get('record_id')
    if not rid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        ExamRecord.objects.get(record_id=int(rid)).delete()
        return Response({'success': True})
    except Exception:
        return Response({'success': False, 'error_msg': '记录不存在'})


@api_view(["GET"])  # 用户列表
def api_manage_student_list(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role not in ('老师', '管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    # 基础查询参数
    username = (request.query_params.get('username') or '').strip()
    classroom = (request.query_params.get('classroom') or '').strip()
    department = (request.query_params.get('department') or '').strip()
    role = (request.query_params.get('role') or '').strip()
    vip_status = (request.query_params.get('vip_status') or '').strip().lower()  # expiring|expired|valid
    face_status = (request.query_params.get('face_status') or '').strip().lower()  # expiring|expired|valid|missing
    sort_field = (request.query_params.get('sort_field') or '').strip()  # vip_days_left|face_days_left
    sort_dir = (request.query_params.get('sort_dir') or 'asc').strip().lower()
    try:
        page = int(request.query_params.get('page') or 1)
    except Exception:
        page = 1
    try:
        page_size = int(request.query_params.get('page_size') or 10)
    except Exception:
        page_size = 10
    page_size = max(1, min(200, page_size))

    from django.utils import timezone
    now = timezone.now()
    soon = now + _td(days=3)  # 替换为 datetime.timedelta

    qs = User.objects.all().order_by('user_id')
    if username:
        qs = qs.filter(username__icontains=username)
    if classroom:
        qs = qs.filter(classroom__icontains=classroom)
    if department:
        qs = qs.filter(department__icontains=department)
    if role:
        qs = qs.filter(role=role)

    # VIP 状态过滤：只针对 VIP 用户
    if vip_status:
        if vip_status == 'expired':
            qs = qs.filter(role='VIP', vip_expires_at__lte=now)
        elif vip_status == 'expiring':
            qs = qs.filter(role='VIP', vip_expires_at__gt=now, vip_expires_at__lte=soon)
        elif vip_status == 'valid':
            qs = qs.filter(role='VIP', vip_expires_at__gt=soon)

    # Face 状态过滤：需要预分类（全部相关用户）
    user_list = list(qs)
    if face_status and FaceProfile is not None:
        fps = FaceProfile.objects.filter(user_id__in=[u.user_id for u in user_list])
        expired_ids, expiring_ids, valid_ids = set(), set(), set()
        for fp in fps:
            exp = getattr(fp, 'expires_at', None)
            if exp is None:
                valid_ids.add(fp.user_id)
            else:
                if exp <= now:
                    expired_ids.add(fp.user_id)
                elif exp <= soon:
                    expiring_ids.add(fp.user_id)
                else:
                    valid_ids.add(fp.user_id)
        if face_status == 'expired':
            user_list = [u for u in user_list if u.user_id in expired_ids]
        elif face_status == 'expiring':
            user_list = [u for u in user_list if u.user_id in expiring_ids]
        elif face_status == 'valid':
            user_list = [u for u in user_list if u.user_id in valid_ids]
        elif face_status == 'missing':
            with_fp = expired_ids | expiring_ids | valid_ids
            user_list = [u for u in user_list if u.user_id not in with_fp]

    # 构建 FaceProfile map（减少重复查询）
    face_map = {}
    if FaceProfile is not None and user_list:
        fps2 = FaceProfile.objects.filter(user_id__in=[u.user_id for u in user_list])
        for fp in fps2:
            exp = getattr(fp, 'expires_at', None)
            if exp is None:
                state = 'valid'
            else:
                if exp <= now:
                    state = 'expired'
                elif exp <= soon:
                    state = 'expiring'
                else:
                    state = 'valid'
            face_map[fp.user_id] = (state, exp)

    rows_full = []
    for u in user_list:
        vip_exp = getattr(u, 'vip_expires_at', None)
        if u.role == 'VIP':
            if vip_exp and vip_exp <= now:
                vip_state = 'expired'
            elif vip_exp and vip_exp <= soon:
                vip_state = 'expiring'
            elif vip_exp:
                vip_state = 'valid'
            else:
                vip_state = 'valid'
        else:
            vip_state = ''
        vip_days_left = None
        if vip_exp and vip_exp > now:
            vip_days_left = max(0, int((vip_exp - now).total_seconds() // 86400))
        fstate, fexp = face_map.get(u.user_id, ('missing', None))
        face_days_left = None
        if isinstance(fexp, _dt) and fstate in {'valid','expiring'} and fexp > now:
            face_days_left = max(0, int((fexp - now).total_seconds() // 86400))
        face_expires_at_str = fexp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(fexp, _dt) else None
        rows_full.append({
            'user_id': u.user_id,
            'username': u.username,
            'role': u.role,
            'department': u.department,
            'classroom': u.classroom,
            'vip_expires_at': vip_exp.strftime('%Y-%m-%d %H:%M:%S') if vip_exp else None,
            'vip_status': vip_state,
            'vip_days_left': vip_days_left,
            'face_status': fstate,
            'face_expires_at': face_expires_at_str,
            'face_days_left': face_days_left,
        })

    if sort_field in {'vip_days_left','face_days_left'}:
        reverse = (sort_dir == 'desc')
        def _key(item):
            v = item.get(sort_field)
            return (v is None, v)  # None 置后
        rows_full.sort(key=_key, reverse=reverse)

    total = len(rows_full)
    start = (page - 1) * page_size
    rows = rows_full[start:start+page_size]
    return Response({'success': True, 'students': rows, 'total': total, 'roles': ['学生','老师','管理员','VIP']})


@api_view(["POST"])  # 用户保存
def api_manage_student_save(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role != '管理员':
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    user_id = request.data.get('user_id') or request.data.get('id')
    username = (request.data.get('username') or '').strip()
    password = (request.data.get('password') or '').strip()
    role = (request.data.get('role') or '').strip() or '学生'
    department = (request.data.get('department') or '').strip()
    classroom = (request.data.get('classroom') or '').strip()

    if not username or len(username) < 3:
        return Response({'success': False, 'error_msg': '用户名长度至少为3个字符'})
    allowed_roles = {'学生','老师','VIP','管理员'}
    if role not in allowed_roles:
        return Response({'success': False, 'error_msg': '角色不合法'})
    if not user_id and role == '管理员':
        return Response({'success': False, 'error_msg': '禁止通过接口创建管理员账号'}, status=403)
    if role == '老师' and not department:
        return Response({'success': False, 'error_msg': '请选择或填写部门'})
    if role == '学生' and not classroom:
        return Response({'success': False, 'error_msg': '请选择或填写班级'})

    if user_id:
        try:
            u = User.objects.get(user_id=int(user_id))
        except Exception:
            return Response({'success': False, 'error_msg': '用户不存在'})
        prev_role = u.role
        u.username = username
        if password:
            u.password = make_password(password)
        u.role = role
        if role == '老师':
            u.department = department
            u.classroom = ''
        elif role == '学生':
            u.classroom = classroom
            u.department = ''
            try:
                u.student_no = username
            except Exception:
                pass
            # 学生降级时清空 VIP 到期
            if prev_role == 'VIP':
                try:
                    u.vip_expires_at = None
                except Exception:
                    pass
        elif role == 'VIP':
            # 若从学生升级到 VIP 且未设置或已过期，设置 30 天滚动到期
            from django.utils import timezone
            from datetime import timedelta
            vip_exp_prev = getattr(u, 'vip_expires_at', None)
            if prev_role != 'VIP' or not vip_exp_prev or timezone.now() > vip_exp_prev:
                try:
                    u.vip_expires_at = timezone.now() + timedelta(days=30)
                except Exception:
                    pass
        u.save()
        return Response({'success': True, 'id': u.user_id})
    else:
        if User.objects.filter(username=username).exists():
            return Response({'success': False, 'error_msg': '用户名已存在'})
        from django.utils import timezone
        from datetime import timedelta
        kwargs = {
            'username': username,
            'password': make_password(password) if password else make_password('123456'),
            'role': role,
            'department': department if role == '老师' else '',
            'classroom': classroom if role == '学生' else '',
        }
        u = User.objects.create(**kwargs)
        if role == 'VIP':
            try:
                u.vip_expires_at = timezone.now() + timedelta(days=30)
                u.save(update_fields=['vip_expires_at'])
            except Exception:
                pass
        if role == '学生':
            try:
                u.student_no = username
                u.save()
            except Exception:
                pass
        return Response({'success': True, 'id': u.user_id})


@api_view(["POST"])  # 删除用户
def api_manage_student_delete(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role != '管理员':
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    rid = request.data.get('id') or request.data.get('user_id')
    if not rid:
        return Response({'success': False, 'error_msg': '缺少ID'})
    try:
        User.objects.get(user_id=int(rid)).delete()
        return Response({'success': True})
    except Exception:
        return Response({'success': False, 'error_msg': '用户不存在'})


@api_view(["GET"])  # 考试签到列表
def api_manage_exam_signins(request):
    uid = request.session.get('user_id')
    if not uid:
        return Response({'success': False, 'error_msg': '未登录'}, status=401)
    try:
        me = User.objects.get(user_id=uid)
    except User.DoesNotExist:
        return Response({'success': False, 'error_msg': '用户不存在'}, status=401)
    if me.role not in ('老师', '管理员'):
        return Response({'success': False, 'error_msg': '无权限'}, status=403)

    exam_id = request.query_params.get('exam_id') or request.query_params.get('id')
    if not exam_id:
        return Response({'success': False, 'error_msg': '缺少考试ID'})
    try:
        exam = Exam.objects.get(exam_id=int(exam_id))
    except Exception:
        return Response({'success': False, 'error_msg': '考试不存在'})

    username = (request.query_params.get('username') or '').strip()
    classroom = (request.query_params.get('classroom') or '').strip()
    success_str = (request.query_params.get('success') or '').strip().lower()
    success_filter = None
    if success_str in ('true', '1', 'yes', 'y'):
        success_filter = True
    elif success_str in ('false', '0', 'no', 'n'):
        success_filter = False

    raw_page_size = request.query_params.get('page_size')
    try:
        page = int(request.query_params.get('page') or 1)
    except Exception:
        page = 1
    if raw_page_size is None:
        page_size = None
    else:
        try:
            page_size = int(raw_page_size)
        except Exception:
            page_size = 10
        page_size = max(1, min(200, page_size))

    students_qs = User.objects.filter(role='学生')
    if username:
        students_qs = students_qs.filter(username__icontains=username)
    if classroom:
        students_qs = students_qs.filter(classroom__icontains=classroom)
    students = list(students_qs)

    if students:
        uid_list = [s.user_id for s in students]
        all_qs = ExamQuestion.objects.none()
        from ..models import ExamSignIn as _ES
        all_qs = _ES.objects.filter(exam=exam, user_id__in=uid_list).select_related('user').order_by('-created_at')
    else:
        from ..models import ExamSignIn as _ES
        all_qs = _ES.objects.none()

    latest_by_user = {}
    for r in all_qs:
        k = r.user_id
        if k not in latest_by_user:
            latest_by_user[k] = r

    rows = []
    for s in students:
        r = latest_by_user.get(s.user_id)
        if r is None:
            status = 'not_signed'
            method = ''
            score = None
            reason = ''
            created_at = None
        else:
            status = 'signed_in' if bool(r.success) else 'failed'
            method = r.method
            score = r.score
            reason = r.reason
            created_at = fmt_dt(r.created_at)
        rows.append({
            'user_id': s.user_id,
            'username': s.username,
            'classroom': s.classroom,
            'status': status,
            'method': method,
            'score': score,
            'reason': reason,
            'created_at': created_at,
        })

    if success_filter is not None:
        if success_filter:
            rows = [it for it in rows if it['status'] == 'signed_in']
        else:
            rows = [it for it in rows if it['status'] in ('failed', 'not_signed')]

    total = len(rows)
    signed_in = sum(1 for it in rows if it['status'] == 'signed_in')
    failed = sum(1 for it in rows if it['status'] == 'failed')
    not_signed = sum(1 for it in rows if it['status'] == 'not_signed')
    counts = { 'signed_in': signed_in, 'failed': failed, 'not_signed': not_signed, 'total': total }

    if page_size is not None:
        start = (page - 1) * page_size
        rows = rows[start:start+page_size]

    return Response({'success': True, 'counts': counts, 'signins': rows, 'items': rows})


@api_view(["GET"])  # 最新题目导入模板（动态生成）
def api_manage_question_template(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    wb = Workbook()
    ws = wb.active
    ws.title = 'questions'
    # 新增：已审核 列
    header = ['分数','题干','A','B','C','D','答案','解析','题型','批次','知识点','一级知识点','已审核']
    ws.append(header)
    # 示例行（可选）
    ws.append([2,'下列选项中属于操作系统核心部分的是（ ）。','内核','应用程序','编译器','外设','A','操作系统核心是内核。','单选',1,'操作系统,内核','操作系统','是'])
    ws.append([3,'以下属于进程同步机制的有（ ）。','信号量','互斥锁','防火墙','条件变量','ABD','信号量/互斥锁/条件变量属于同步机制。','多选',1,'操作系统,进程管理,同步机制','操作系统','否'])
    ws.append([1,'进程与线程是同一概念。','','','','','F','进程是资源分配单位,线程是调度单位。','判断',1,'操作系统,进程管理','操作系统','否'])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="question_import_template.xlsx"'
    return resp


@api_view(["POST"])  # 批量删除题目
def api_manage_question_bulk_delete(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    ids = request.data.get('ids') or request.data.get('id_list') or ''
    if isinstance(ids, str):
        try:
            ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        except Exception:
            ids = []
    elif isinstance(ids, list):
        tmp = []
        for x in ids:
            try:
                tmp.append(int(x))
            except Exception:
                pass
        ids = tmp
    else:
        ids = []
    if not ids:
        return Response({'success': False, 'error_msg': '缺少有效ID列表'})
    qs = Question.objects.filter(question_id__in=ids)
    count = qs.count()
    qs.delete()
    return Response({'success': True, 'deleted': count})


@api_view(["POST"])  # 批量标记题目为（未）审核
def api_manage_question_bulk_mark_reviewed(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    ids = request.data.get('ids') or request.data.get('question_ids') or ''
    reviewed_val = request.data.get('reviewed')
    # 解析ID列表
    if isinstance(ids, str):
        try:
            ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        except Exception:
            ids = []
    elif isinstance(ids, list):
        tmp = []
        for x in ids:
            try:
                tmp.append(int(x))
            except Exception:
                pass
        ids = tmp
    else:
        ids = []
    if not ids:
        return Response({'success': False, 'error_msg': '缺少有效题目ID列表'})
    # 解析 reviewed 布尔
    s = str(reviewed_val).strip().lower()
    if s in {'1','true','yes','y','on','已审核','是'}:
        flag = True
    elif s in {'0','false','no','n','off','未审核','否'}:
        flag = False
    else:
        # 默认为 True
        flag = True
    qs = Question.objects.filter(question_id__in=ids)
    changed = 0
    for q in qs:
        try:
            if bool(getattr(q, 'reviewed', False)) != flag:
                q.reviewed = flag
                q.save(update_fields=['reviewed'])
                changed += 1
        except Exception:
            pass
    return Response({'success': True, 'changed': changed, 'reviewed': flag, 'count': qs.count()})


@api_view(["GET"])  # 批次统计（题目数与总分）
def api_manage_batch_stats(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    batches_param = request.query_params.get('batches') or ''
    try:
        if batches_param.strip():
            target = [int(x) for x in batches_param.split(',') if x.strip().isdigit()]
        else:
            raw = Question.objects.values_list('batch', flat=True)
            target = sorted({int(b) for b in raw if isinstance(b, int) and b is not None})
    except Exception:
        target = []
    rows = []
    if target:
        qs = Question.objects.filter(batch__in=target)
        agg = {}
        for q in qs:
            b = getattr(q, 'batch', None)
            if b in (None, ''):
                continue
            try:
                bi = int(b)
            except Exception:
                continue
            if bi not in agg:
                agg[bi] = { 'batch': bi, 'question_count': 0, 'total_score': 0 }
            agg[bi]['question_count'] += 1
            try:
                agg[bi]['total_score'] += int(getattr(q, 'score', 0) or 0)
            except Exception:
                pass
        rows = [agg[b] for b in sorted(agg.keys())]
    return Response({'success': True, 'batches': rows})


@api_view(["POST"])  # 新建批次（将选中题目归入同一批次）
def api_manage_batch_create(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    # question_ids: list/int字符串, 可选 batch 指定批次号；否则自动分配 新= max(合法batch)+1 或 1
    # mode: move(默认) 移动题目；copy 复制题目到新批次（原题保留，实现一个题内容出现在多个批次）
    qids = request.data.get('question_ids') or request.data.get('ids') or []
    batch_param = request.data.get('batch')
    mode = (request.data.get('mode') or 'move').strip().lower()
    if mode not in {'move','copy'}:
        mode = 'move'
    # 解析题目ID列表
    if isinstance(qids, str):
        try:
            qids = [int(x) for x in qids.split(',') if x.strip().isdigit()]
        except Exception:
            qids = []
    elif isinstance(qids, list):
        tmp = []
        for x in qids:
            try: tmp.append(int(x))
            except Exception: pass
        qids = tmp
    else:
        qids = []
    if not qids:
        return Response({'success': False, 'error_msg': '题目列表不能为空'})
    # 计算批次号
    if batch_param not in (None, '', []):
        try:
            batch_no = int(batch_param)
            if batch_no <= 0:
                raise ValueError
        except Exception:
            return Response({'success': False, 'error_msg': '批次号无效'})
    else:
        raw = Question.objects.values_list('batch', flat=True)
        valid_nums = []
        for b in raw:
            try:
                s = str(b).strip()
                if s and s.isdigit():
                    iv = int(s)
                    if iv>0: valid_nums.append(iv)
            except Exception:
                pass
        batch_no = (max(valid_nums)+1) if valid_nums else 1
    qs = Question.objects.filter(question_id__in=qids)
    updated = 0
    copied = 0
    if mode == 'move':
        for q in qs:
            try:
                q.batch = batch_no
                q.save(update_fields=['batch'])
                updated += 1
            except Exception:
                pass
    else:  # copy
        fields = ['question_type','A_answer','B_answer','C_answer','D_answer','content','answer','score','analysis','knowledge_points','primary_knowledge']
        for q in qs:
            try:
                data = {f: getattr(q, f) for f in fields}
                data['batch'] = batch_no
                Question.objects.create(**data)
                copied += 1
            except Exception:
                pass
    if updated==0 and copied==0:
        return Response({'success': False, 'error_msg': '未找到有效题目或操作未生效'})
    return Response({'success': True, 'batch': batch_no, 'mode': mode, 'updated': updated, 'copied': copied})


@api_view(["GET"])  # 批次调试：返回每个批次题目数量
def api_manage_batch_debug(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    agg = {}
    qs = Question.objects.all().only('batch')
    for q in qs:
        b = getattr(q, 'batch', None)
        try:
            if b is None:
                continue
            bi = int(b)
            agg[bi] = agg.get(bi, 0) + 1
        except Exception:
            continue
    return Response({'success': True, 'batches': sorted(list(agg.keys())), 'counts': agg, 'total_questions': qs.count()})


@api_view(["GET"])  # 评论管理列表（老师/管理员）
def api_manage_q_comments(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qs = QuestionComment.objects.select_related('user', 'question').order_by('-id')
    qid = request.query_params.get('question_id')
    uid = request.query_params.get('user_id')
    keyword = request.query_params.get('keyword') or request.query_params.get('q') or ''
    try:
        if qid not in (None, '', 'null'):
            qs = qs.filter(question_id=int(qid))
    except Exception:
        pass
    try:
        if uid not in (None, '', 'null'):
            qs = qs.filter(user_id=int(uid))
    except Exception:
        pass
    if keyword.strip():
        qs = qs.filter(content__icontains=keyword.strip())
    try:
        limit = int(request.query_params.get('limit') or 50)
    except Exception:
        limit = 50
    limit = max(1, min(200, limit))
    items = []
    for c in qs[:limit]:
        u = c.user
        q = c.question
        uname = (getattr(u, 'nickname', '') or '').strip() or (getattr(u, 'username', '') or '').strip() or '匿名用户'
        items.append({
            'id': c.id,
            'question_id': getattr(q, 'question_id', None),
            'question_snippet': (getattr(q, 'content', '') or '')[:80],
            'user_id': getattr(u, 'user_id', None),
            'username': uname,
            'content': c.content,
            'created_at': fmt_dt(c.created_at)
        })
    return Response({'success': True, 'items': items})


@api_view(["POST"])  # 评论删除（老师/管理员）
def api_manage_q_comment_delete(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    cid = request.data.get('id')
    try:
        cid = int(cid)
    except Exception:
        return Response({'success': False, 'error_msg': '无效的ID'})
    c = QuestionComment.objects.filter(id=cid).first()
    if not c:
        return Response({'success': False, 'error_msg': '评论不存在'})
    c.delete()
    return Response({'success': True})


@api_view(["GET"])  # 全局：人脸与VIP概览（教师/管理员）
def api_manage_face_overview(request):
    user, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    from django.utils import timezone
    now = timezone.now()
    stu_q = User.objects.filter(role__in=['学生','VIP'])
    total_students = stu_q.count()
    vip_q = User.objects.filter(role='VIP')
    vip_count = vip_q.filter(vip_expires_at__gt=now).count()
    vip_expiring_3d = vip_q.filter(vip_expires_at__gt=now, vip_expires_at__lte=now + _td(days=3)).count()
    face_total = 0
    face_valid = 0
    face_expiring_3d = 0
    face_expired = 0
    if FaceProfile is not None:
        fps = FaceProfile.objects.filter(user__role__in=['学生','VIP']).select_related('user')
        face_total = fps.count()
        for fp in fps:
            exp = getattr(fp, 'expires_at', None)
            if not exp:
                face_valid += 1
                continue
            if exp <= now:
                face_expired += 1
            else:
                face_valid += 1
                if exp <= now + _td(days=3):
                    face_expiring_3d += 1
    face_missing = max(0, total_students - face_total)
    face_required = False
    if GlobalSetting is not None:
        try:
            row = GlobalSetting.objects.filter(key='FACE_REQUIRED').first()
            face_required = bool(row and str(row.value).strip() in {'1','true','yes','on'})
        except Exception:
            pass
    attention_total = vip_expiring_3d + face_expiring_3d + face_expired
    return Response({
        'success': True,
        'total_students': total_students,
        'vip_count': vip_count,
        'vip_expiring_3d': vip_expiring_3d,
        'face_total': face_total,
        'face_valid': face_valid,
        'face_expiring_3d': face_expiring_3d,
        'face_expired': face_expired,
        'face_missing': face_missing,
        'face_required': face_required,
        'attention_total': attention_total,
    })


# 新增：审查共识阈值（老师/管理员可配置）
@api_view(["GET"])  # 获取当前共识阈值
def api_manage_review_consensus(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    default_th = 5
    try:
        row = GlobalSetting.objects.filter(key='REVIEW_CONSENSUS').first() if GlobalSetting else None
        val = int(str(row.value).strip()) if row and str(row.value).strip() else default_th
    except Exception:
        val = default_th
    # 规范范围
    val = 3 if val < 3 else (50 if val > 50 else val)
    return Response({'success': True, 'threshold': val})


@api_view(["POST"])  # 保存共识阈值（3~50）
def api_manage_review_consensus_save(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    try:
        raw = request.data.get('threshold')
        val = int(str(raw).strip())
        if val < 3: val = 3
        if val > 50: val = 50
    except Exception:
        return Response({'success': False, 'error_msg': '阈值需为数字(3~50)'}, status=400)
    if GlobalSetting is None:
        return Response({'success': False, 'error_msg': '配置存储不可用'}, status=500)
    row, _ = GlobalSetting.objects.get_or_create(key='REVIEW_CONSENSUS', defaults={'value': str(val)})
    row.value = str(val)
    row.save(update_fields=['value'])
    return Response({'success': True, 'threshold': val})


@api_view(["POST"])  # 批量降级 VIP -> 学生
def api_manage_students_batch_degrade_vip(request):
    user, err = require_login(request, roles=['管理员'])
    if err: return err
    ids = request.data.get('user_ids') or request.data.get('ids') or []
    if isinstance(ids, str):
        try:
            ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        except Exception:
            ids = []
    elif isinstance(ids, list):
        ids = [int(x) for x in ids if str(x).isdigit()]
    else:
        ids = []
    if not ids:
        return Response({'success': False, 'error_msg': '缺少用户ID列表'})
    changed = 0
    for u in User.objects.filter(user_id__in=ids, role='VIP'):
        u.role = '学生'
        u.vip_expires_at = None
        try:
            u.save(update_fields=['role','vip_expires_at'])
            changed += 1
        except Exception:
            pass
    return Response({'success': True, 'changed': changed})


@api_view(["GET"])  # 人脸即将到期/已过期列表
def api_manage_face_expiring(request):
    user, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    try:
        days = int(request.query_params.get('days') or 3)
    except Exception:
        days = 3
    from django.utils import timezone
    now = timezone.now()
    soon = now + _td(days=days)
    out = []
    if FaceProfile is not None:
        fps = FaceProfile.objects.filter(user__role__in=['学生','VIP']).select_related('user')
        for fp in fps:
            exp = getattr(fp, 'expires_at', None)
            state = 'valid'
            if exp:
                if exp <= now:
                    state = 'expired'
                elif exp <= soon:
                    state = 'expiring'
            else:
                state = 'valid'
            if state in {'expiring','expired'}:
                days_left = None
                if state == 'expiring' and exp:
                    days_left = max(0, int((exp - now).total_seconds() // 86400))
                out.append({
                    'user_id': fp.user_id,
                    'username': getattr(fp.user,'username',None),
                    'state': state,
                    'expires_at': exp.strftime('%Y-%m-%d %H:%M:%S') if exp else None,
                    'days_left': days_left,
                })
    return Response({'success': True, 'items': out, 'days': days})


@api_view(["GET"])  # 待审核题目队列（考纲/解析缺失或未审核）
def api_manage_review_queue(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    try:
        limit = int(request.query_params.get('limit') or 100)
    except Exception:
        limit = 100
    limit = max(1, min(500, limit))
    # 过滤条件：默认仅缺失项或未审核；可通过 missing_only=0 查看全部并排序优先缺失
    missing_only = str(request.query_params.get('missing_only') or '1').strip().lower() in {'1','true','yes','y'}
    # 可选筛选：按批次或题型
    batch_param = request.query_params.get('batch')
    types_param = request.query_params.get('types') or request.query_params.get('type')

    from django.db.models import Q
    qs = Question.objects.all().order_by('question_id')
    # 待审核条件
    cond_missing = Q(knowledge_points__isnull=True) | Q(knowledge_points='') | \
                   Q(primary_knowledge__isnull=True) | Q(primary_knowledge='') | \
                   Q(analysis__isnull=True) | Q(analysis='')
    cond_unreviewed = Q(reviewed=False)
    cond = cond_missing | cond_unreviewed
    if missing_only:
        qs = qs.filter(cond)
    # 其它筛选
    if batch_param not in (None, '', 'null'):
        try:
            qs = qs.filter(batch=int(batch_param))
        except Exception:
            pass
    if types_param:
        tlist = [t.strip() for t in str(types_param).split(',') if t.strip()]
        if tlist:
            qs = qs.filter(question_type__in=tlist)

    rows = []
    stats = {'total': 0, 'missing_kp': 0, 'missing_primary': 0, 'missing_analysis': 0, 'unreviewed': 0}
    for q in qs[:limit]:
        miss_kp = not bool(q.knowledge_points)
        miss_pk = not bool(q.primary_knowledge)
        miss_ana = not bool(q.analysis)
        unrev = not bool(getattr(q, 'reviewed', False))
        reasons = []
        if miss_kp: reasons.append('考纲大类为空')
        if miss_pk: reasons.append('一级知识点为空')
        if miss_ana: reasons.append('解析为空')
        if unrev: reasons.append('未审核')
        stats['total'] += 1
        if miss_kp: stats['missing_kp'] += 1
        if miss_pk: stats['missing_primary'] += 1
        if miss_ana: stats['missing_analysis'] += 1
        if unrev: stats['unreviewed'] += 1
        rows.append({
            'id': q.question_id,
            'question_type': q.question_type,
            'content': q.content if len(q.content) <= 200 else (q.content[:200] + '…'),
            'batch': q.batch,
            'reviewed': not unrev,
            'missing_kp': miss_kp,
            'missing_primary': miss_pk,
            'missing_analysis': miss_ana,
            'reasons': reasons,
        })
    return Response({'success': True, 'items': rows, 'stats': stats, 'limit': limit})
