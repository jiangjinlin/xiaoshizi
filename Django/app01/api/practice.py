import random
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Question, PracticeAnswer
from .utils import require_login  # removed enforce_face_required for practice endpoints
# 新增：考纲条目，用于按省份/专业过滤练习题
try:
    from ..models import SyllabusItem
except Exception:
    SyllabusItem = None


@api_view(["GET"])  # 练习可选项（仅统计已审核题目）
def api_practice_options(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    # 可选：按省份/专业限制题库范围
    province = (request.query_params.get('province') or '').strip()
    major = (request.query_params.get('major') or '').strip()
    # 若未显式传参，则回退到会话选择
    if not province:
        province = (request.session.get('syllabus_province') or '').strip()
    if not major:
        major = (request.session.get('syllabus_major') or '').strip()
    allowed_kp = set()
    allowed_primary = set()
    if SyllabusItem is not None and province and major:
        try:
            rows = SyllabusItem.objects.filter(province=province, major=major)
            allowed_kp = set(r.kp.strip() for r in rows if getattr(r, 'kp', '').strip())
            allowed_primary = set(r.primary.strip() for r in rows if getattr(r, 'primary', '').strip())
        except Exception:
            allowed_kp = set()
            allowed_primary = set()
    qs = Question.objects.filter(reviewed=True)
    # 若选择了省份/专业，则仅保留落在该考纲的题
    if allowed_kp or allowed_primary:
        qlist = []
        for q in qs:
            ok = False
            if q.primary_knowledge and q.primary_knowledge.strip() in allowed_primary:
                ok = True
            if not ok and q.knowledge_points:
                raw = q.knowledge_points.replace('，', ',')
                for part in raw.split(','):
                    if part.strip() and part.strip() in allowed_kp:
                        ok = True
                        break
            if ok:
                qlist.append(q)
        qs = qlist
    type_counts = {}
    batches = set()
    scores = set()
    for q in qs:
        if q.question_type in ('单选', '多选', '判断'):
            type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
            if getattr(q, 'batch', None) is not None:
                batches.add(q.batch)
            if isinstance(getattr(q, 'score', None), (int, float)):
                scores.add(q.score)
    types = [t for t in ['单选', '多选', '判断'] if type_counts.get(t, 0) > 0]
    counts_by_type = {k: int(v) for k, v in type_counts.items()}
    batches_list = sorted(batches)
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    return Response({'success': True,
                     'types': types,
                     'batches': batches_list,
                     'counts_by_type': counts_by_type,
                     'score_range': {'min': min_score, 'max': max_score},
                     'total': sum(type_counts.values())})


@api_view(["GET", "POST"])  # 抽题（仅使用已审核题目）
def api_practice_questions(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    uid = user.user_id

    # 题型（多选）
    raw_types = request.query_params.get('types') or request.data.get('types')
    if raw_types:
        qtypes = [s.strip() for s in str(raw_types).split(',') if s.strip()]
    else:
        qtypes_single = request.query_params.get('type') or request.data.get('type') or ''
        qtypes = [qtypes_single] if qtypes_single else []
    if not qtypes:
        qtypes = ['单选', '多选', '判断']

    # 多批次
    batches_param = request.query_params.get('batches') or request.data.get('batches') or ''
    batch_list = []
    if batches_param:
        for part in str(batches_param).split(','):
            part = part.strip()
            if part.isdigit():
                batch_list.append(int(part))
    # 单批次兼容
    single_batch = request.query_params.get('batch') or request.data.get('batch')
    try:
        if single_batch not in (None, '', []):
            b = int(single_batch)
            if b not in batch_list:
                batch_list.append(b)
    except Exception:
        pass

    # 数量
    try:
        limit = int(request.query_params.get('limit') or request.query_params.get('count') or request.data.get('limit') or request.data.get('count') or 10)
    except Exception:
        limit = 10
    limit = max(1, min(200, limit))

    # 难度区间
    try:
        score_min = int(request.query_params.get('score_min') or request.data.get('score_min') or 0)
    except Exception:
        score_min = 0
    try:
        score_max = int(request.query_params.get('score_max') or request.data.get('score_max') or 0)
    except Exception:
        score_max = 0
    if score_max and score_min and score_max < score_min:
        score_min, score_max = score_max, score_min

    # 错题再练
    wrong_only = str(request.query_params.get('wrong_only') or request.data.get('wrong_only') or '').lower() in {'1','true','yes','y'}

    # 可选：按省份/专业限制题库范围
    province = (request.query_params.get('province') or request.data.get('province') or '').strip()
    major = (request.query_params.get('major') or request.data.get('major') or '').strip()
    # 若未显式传参，则回退到会话选择
    if not province:
        province = (request.session.get('syllabus_province') or '').strip()
    if not major:
        major = (request.session.get('syllabus_major') or '').strip()
    allowed_kp = set()
    allowed_primary = set()
    if SyllabusItem is not None and province and major:
        try:
            rows = SyllabusItem.objects.filter(province=province, major=major)
            allowed_kp = set(r.kp.strip() for r in rows if getattr(r, 'kp', '').strip())
            allowed_primary = set(r.primary.strip() for r in rows if getattr(r, 'primary', '').strip())
        except Exception:
            allowed_kp = set()
            allowed_primary = set()

    qs = Question.objects.filter(reviewed=True, question_type__in=qtypes)
    if batch_list:
        qs = qs.filter(batch__in=batch_list)
    if score_min:
        qs = qs.filter(score__gte=score_min)
    if score_max:
        qs = qs.filter(score__lte=score_max)

    if wrong_only:
        wrong_qids = list(PracticeAnswer.objects.filter(user_id=uid, last_is_correct=False).values_list('question_id', flat=True))
        if not wrong_qids:
            return Response({'success': True, 'questions': [], 'message': '暂无错题'})
        qs = qs.filter(question_id__in=wrong_qids)

    qlist = list(qs)

    # 若选择了省份/专业，则仅保留落在该考纲的题
    if qlist and (allowed_kp or allowed_primary):
        filtered = []
        for q in qlist:
            ok = False
            if q.primary_knowledge and q.primary_knowledge.strip() in allowed_primary:
                ok = True
            if not ok and q.knowledge_points:
                raw = q.knowledge_points.replace('，', ',')
                for part in raw.split(','):
                    if part.strip() and part.strip() in allowed_kp:
                        ok = True
                        break
            if ok:
                filtered.append(q)
        qlist = filtered

    if not qlist:
        return Response({'success': True, 'questions': []})
    if len(qlist) <= limit:
        picked = qlist[:]
        random.shuffle(picked)
    else:
        picked = random.sample(qlist, limit)

    out = []
    for q in picked:
        options = []
        if q.question_type in ['单选', '多选']:
            for key, label in zip(['A', 'B', 'C', 'D'], [q.A_answer, q.B_answer, q.C_answer, q.D_answer]):
                if label:
                    options.append({'key': key, 'label': label})
        elif q.question_type == '判断':
            options = [{'key': 'A', 'label': '正确'}, {'key': 'B', 'label': '错误'}]
        out.append({
            'id': q.question_id,
            'type': q.question_type,
            'content': q.content,
            'options': options,
            'score': q.score,
            'analysis': q.analysis or '',
            'knowledge_points': q.knowledge_points or '',  # 考纲知识点（大类）
            'primary_knowledge': q.primary_knowledge or ''  # 一级知识点
        })

    return Response({'success': True, 'questions': out})


@api_view(["POST"])  # 判题并写入练习统计
def api_practice_check(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    uid = user.user_id

    answers = request.data.get('answers')
    if isinstance(answers, str):
        try:
            import json
            answers = json.loads(answers)
        except Exception:
            answers = None
    amap = {}
    if isinstance(answers, dict):
        for k, v in answers.items():
            amap[str(k)] = v
    for k, v in request.data.items():
        if str(k).startswith('answer_'):
            qid = str(k).replace('answer_', '')
            amap[qid] = v

    try:
        ids = [int(k) for k in amap.keys() if str(k).isdigit()]
    except Exception:
        ids = []
    qs_map = {q.question_id: q for q in Question.objects.filter(question_id__in=ids)} if ids else {}

    details = []
    correct = 0
    total = 0
    for qid_str, ua in amap.items():
        try:
            qid = int(qid_str)
        except Exception:
            continue
        q = qs_map.get(qid)
        if not q or q.question_type not in ('单选', '多选', '判断'):
            continue
        total += 1
        ca = str(q.answer or '')
        ok = False
        if q.question_type == '单选':
            ok = str(ua).strip().upper() == ca.strip().upper()
        elif q.question_type == '多选':
            if isinstance(ua, list):
                uset = set([str(x).strip().upper() for x in ua if str(x).strip()])
            else:
                import re as _re
                letters = _re.findall(r'[A-D]', str(ua).upper())
                uset = set([x.strip().upper() for x in letters])
            import re as _re2
            cset = set([x for x in _re2.findall(r'[A-D]', ca.upper())])
            ok = (uset == cset)
        else:
            s = str(ua).strip().lower()
            ok = s in {'a','t','true','yes','y','1','对','正确','是'} if ca.strip().lower() in {'a','t','true','yes','y','1','对','正确','是'} else s in {'b','f','false','no','n','0','错','错误','否'}
        if ok:
            correct += 1
        details.append({
            'id': qid,
            'question_id': qid,
            'type': q.question_type,
            'content': q.content,
            'user_answer': ua,
            'correct_answer': ca,
            'is_correct': bool(ok),
            'analysis': q.analysis or '',
            'knowledge_points': q.knowledge_points or '',
            'primary_knowledge': q.primary_knowledge or ''
        })
        # 更新练习统计
        if uid:
            pa, _ = PracticeAnswer.objects.get_or_create(user_id=uid, question_id=qid, defaults={'total_attempts':0,'correct_attempts':0,'last_is_correct':False})
            pa.total_attempts += 1
            if ok:
                pa.correct_attempts += 1
            pa.last_is_correct = bool(ok)
            pa.save()

    accuracy = round(100.0 * correct / total, 0) if total else 0
    return Response({'success': True, 'correct': correct, 'total': total, 'accuracy': accuracy, 'details': details})


@api_view(["GET"])  # 练习统计（题型正确率与错题数）
def api_practice_stats(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    uid = user.user_id
    qtypes = ['单选','多选','判断']
    stats = {}
    for t in qtypes:
        qids = list(Question.objects.filter(reviewed=True, question_type=t).values_list('question_id', flat=True))
        if not qids:
            continue
        pas = PracticeAnswer.objects.filter(user_id=uid, question_id__in=qids)
        total_att = sum(p.total_attempts for p in pas)
        correct_att = sum(p.correct_attempts for p in pas)
        acc = round(100.0 * correct_att / total_att, 1) if total_att else None
        stats[t] = {'accuracy': acc, 'attempts': total_att}
    wrong_count = PracticeAnswer.objects.filter(user_id=uid, last_is_correct=False).count()
    return Response({'success': True, 'types': stats, 'wrong_count': wrong_count})


@api_view(["GET"])  # 错题列表（最近错误优先）
def api_practice_mistakes(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    uid = user.user_id
    try:
        limit = int(request.query_params.get('limit') or 50)
    except Exception:
        limit = 50
    limit = max(1, min(200, limit))
    pas = PracticeAnswer.objects.filter(user_id=uid, last_is_correct=False).order_by('-last_answer_time')[:limit]
    qids = [p.question_id for p in pas]
    qmap = {q.question_id: q for q in Question.objects.filter(question_id__in=qids, reviewed=True)}
    out=[]
    for p in pas:
        q = qmap.get(p.question_id)
        if not q: continue
        out.append({'id': q.question_id, 'type': q.question_type, 'content': q.content, 'score': q.score, 'batch': q.batch, 'knowledge_points': q.knowledge_points or '', 'primary_knowledge': q.primary_knowledge or ''})
    return Response({'success': True, 'questions': out})
