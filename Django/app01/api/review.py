from django.db import transaction
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Question, QuestionReview, User
# 新增：可配置的共识阈值
try:
    from ..models import GlobalSetting  # 可选：不存在时回退默认
except Exception:  # pragma: no cover
    GlobalSetting = None
from .utils import require_login


def _normalize_answer(qtype, ans):
    s = str(ans or '').strip().upper()
    if not s:
        return ''
    if qtype in ('单选', '判断'):
        # 统一到 A/B（判断：A=正确，B=错误）
        if s in {'A','B','C','D'}:
            return s
        if s in {'T','TRUE','Y','YES','1','对','正确','是'}:
            return 'A'
        if s in {'F','FALSE','N','NO','0','错','错误','否'}:
            return 'B'
        return s[:1]
    # 多选：提取 A-D，去重排序
    import re
    letters = re.findall(r'[A-D]', s)
    uniq = sorted(set([x.strip().upper() for x in letters if x.strip()]))
    return ''.join(uniq)


# 新增：读取共识阈值（默认5，范围3~50）
_DEF_CONS_TH = 5

def _get_consensus_threshold() -> int:
    try:
        if GlobalSetting is None:
            return _DEF_CONS_TH
        row = GlobalSetting.objects.filter(key='REVIEW_CONSENSUS').first()
        if not row:
            return _DEF_CONS_TH
        v = int(str(row.value).strip())
        if v < 3: v = 3
        if v > 50: v = 50
        return v
    except Exception:
        return _DEF_CONS_TH


def _build_question_payload(q):
    options = []
    if q.question_type in ('单选','多选'):
        for key, label in zip(['A','B','C','D'], [q.A_answer, q.B_answer, q.C_answer, q.D_answer]):
            if label:
                options.append({'key': key, 'label': label})
    elif q.question_type == '判断':
        options = [{'key':'A','label':'正确'},{'key':'B','label':'错误'}]
    return {
        'id': q.question_id,
        'type': q.question_type,
        'content': q.content,
        'options': options,
        'current_answer': q.answer or '',
        'current_kp': q.knowledge_points or '',
        'current_primary': q.primary_knowledge or '',
        'current_analysis': q.analysis or ''
    }


@api_view(["GET"])  # 获取下一道待审题目（支持筛选：pending/conflict/kp，默认仅未审核 reviewed=False）
def api_review_next(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    uid = user.user_id
    reviewed_qids = list(QuestionReview.objects.filter(user_id=uid).values_list('question_id', flat=True))

    # 过滤条件
    pending_only = str(request.query_params.get('pending_only') or '').lower() in {'1','true','yes','y'}
    conflict_only = str(request.query_params.get('conflict_only') or '').lower() in {'1','true','yes','y'}
    batch_param = request.query_params.get('batch')
    kp_filter = (request.query_params.get('kp') or request.query_params.get('knowledge') or '').strip()
    reviewed_param = str(request.query_params.get('reviewed') or '').lower()

    base_qs = Question.objects.filter(question_type__in=('单选','多选','判断')).exclude(question_id__in=reviewed_qids)
    # 新增：默认仅返回未审核题目；若显式传入 reviewed=1/true 才返回已审核
    if reviewed_param in {'1','true','yes','y'}:
        base_qs = base_qs.filter(reviewed=True)
    else:
        base_qs = base_qs.filter(reviewed=False)

    if batch_param not in (None, ''):
        try:
            base_qs = base_qs.filter(batch=int(batch_param))
        except Exception:
            pass
    if kp_filter:
        base_qs = base_qs.filter(knowledge_points__icontains=kp_filter)

    candidates = list(base_qs)
    if not candidates:
        return Response({'success': True, 'question': None})

    # pending/conflict 计算（在候选集合上）
    if pending_only or conflict_only:
        qids = [q.question_id for q in candidates]
        # 统计每题每种建议的计数
        grouped = (QuestionReview.objects.filter(question_id__in=qids)
                   .values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                   .annotate(c=Count('id')))
        by_q = {}
        for g in grouped:
            arr = by_q.setdefault(g['question_id'], [])
            arr.append(int(g['c']))
        filtered = []
        cons_th = _get_consensus_threshold()
        for q in candidates:
            arr = by_q.get(q.question_id, [])
            has_consensus = any(x >= cons_th for x in arr)
            has_conflict = (len(arr) >= 2 and not has_consensus)
            if pending_only and (not has_consensus):
                filtered.append(q)
            elif conflict_only and has_conflict:
                filtered.append(q)
        candidates = filtered
        if not candidates:
            return Response({'success': True, 'question': None})

    # 优先缺少标注的题
    need_qs = [q for q in candidates if not (q.knowledge_points and q.primary_knowledge and q.analysis)]
    pool = need_qs if need_qs else candidates
    import random as _rnd
    q = _rnd.choice(pool)
    return Response({'success': True, 'question': _build_question_payload(q)})


@api_view(["POST"])  # 提交审查意见，并在达成共识时自动更新题库
@transaction.atomic
def api_review_submit(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    try:
        qid = int(request.data.get('question_id'))
    except Exception:
        return Response({'success': False, 'error_msg': '缺少或非法的 question_id'}, status=400)
    try:
        q = Question.objects.get(question_id=qid)
    except Question.DoesNotExist:
        return Response({'success': False, 'error_msg': '题目不存在'}, status=404)

    s_answer = _normalize_answer(q.question_type, request.data.get('suggested_answer'))
    s_kp = (request.data.get('suggested_kp') or '').strip()
    s_primary = (request.data.get('suggested_primary') or '').strip()
    s_analysis = (request.data.get('suggested_analysis') or '').strip()
    answer_wrong = str(request.data.get('answer_wrong') or '').lower() in {'1','true','yes','y'}

    if q.question_type in ('单选','判断') and s_answer not in {'A','B','C','D',''}:
        return Response({'success': False, 'error_msg': '答案需为 A-D'}, status=400)

    # upsert 用户审查记录
    obj, created = QuestionReview.objects.select_for_update().get_or_create(
        user_id=user.user_id, question_id=qid,
        defaults={
            'suggested_answer': s_answer,
            'suggested_kp': s_kp,
            'suggested_primary': s_primary,
            'suggested_analysis': s_analysis,
            'answer_wrong': answer_wrong,
        }
    )
    if not created:
        obj.suggested_answer = s_answer
        obj.suggested_kp = s_kp
        obj.suggested_primary = s_primary
        obj.suggested_analysis = s_analysis
        obj.answer_wrong = answer_wrong
        obj.save()

    # 统计共识（答案/考纲/一级知识点/错误标记 一致即视为同一种）
    group = QuestionReview.objects.filter(question_id=qid,
        suggested_answer=s_answer,
        suggested_kp=s_kp,
        suggested_primary=s_primary,
        answer_wrong=answer_wrong
    )
    count = group.count()
    promoted = False
    cons_th = _get_consensus_threshold()
    if count >= cons_th:
        # 选择一个较优解析（最长的非空）
        analyses = [r.suggested_analysis.strip() for r in group if r.suggested_analysis and r.suggested_analysis.strip()]
        best_analysis = max(analyses, key=len) if analyses else (q.analysis or '')
        # 若标记原答案有误，则用建议答案覆盖；否则仅在题库原字段为空时补充
        if answer_wrong:
            q.answer = s_answer or (q.answer or '')
        else:
            if not (q.answer or ''):
                q.answer = s_answer
        if s_kp:
            q.knowledge_points = s_kp
        if s_primary:
            q.primary_knowledge = s_primary
        if best_analysis and (not q.analysis or answer_wrong):
            q.analysis = best_analysis
        # 新增：达成共识则标记为已审核
        try:
            q.reviewed = True
        except Exception:
            pass
        q.save()
        promoted = True

    return Response({'success': True, 'consensus_count': count, 'promoted': promoted, 'consensus_threshold': cons_th})


@api_view(["GET"])  # 贡献度排行榜（按提交数与共识数加权）
def api_review_rank(request):
    user, err = require_login(request, roles=['学生','VIP'])
    if err: return err
    # 总提交数
    agg = QuestionReview.objects.values('user_id').annotate(total=Count('id')).order_by('-total')
    user_ids = [a['user_id'] for a in agg]
    umap = {u.user_id: u for u in User.objects.filter(user_id__in=user_ids)}
    # 共识集合（达到阈值的组）
    cons_th = _get_consensus_threshold()
    consensus = (QuestionReview.objects.values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
                 .annotate(c=Count('id')).filter(c__gte=cons_th))
    cons_set = set()
    for r in consensus:
        cons_set.add((r['question_id'], r['suggested_answer'] or '', r['suggested_kp'] or '', r['suggested_primary'] or '', bool(r['answer_wrong'])))
    # 统计每个用户的共识命中数
    cons_count_map = {}
    if cons_set:
        # 为避免超大计算，分批用户遍历（当前规模一般可直接处理）
        for uid in user_ids:
            reviews = QuestionReview.objects.filter(user_id=uid).values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
            cnt = 0
            for rv in reviews:
                key = (rv['question_id'], rv['suggested_answer'] or '', rv['suggested_kp'] or '', rv['suggested_primary'] or '', bool(rv['answer_wrong']))
                if key in cons_set:
                    cnt += 1
            cons_count_map[uid] = cnt
    out = []
    for a in agg[:50]:
        uid = a['user_id']
        u = umap.get(uid)
        total = int(a['total'])
        consensus_count = int(cons_count_map.get(uid, 0))
        score = total + 2 * consensus_count
        out.append({
            'user_id': uid,
            'username': u.username if u else f'u{uid}',
            'total': total,
            'consensus': consensus_count,
            'score': score,
        })
    # 按 score 再排一次
    out.sort(key=lambda x: (-x['score'], -x['total']))
    return Response({'success': True, 'rank': out, 'consensus_threshold': cons_th})


@api_view(["GET"])  # 管理端：每题审查统计与分歧
def api_manage_review_stats(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    try:
        limit = int(request.query_params.get('limit') or 50)
    except Exception:
        limit = 50
    limit = max(1, min(200, limit))
    qid = request.query_params.get('question_id')

    base = QuestionReview.objects.all()
    if qid and str(qid).isdigit():
        base = base.filter(question_id=int(qid))

    # 聚合每题的总审查数
    totals = base.values('question_id').annotate(total=Count('id')).order_by('-total')
    qids = [t['question_id'] for t in totals[:limit]]
    qmap = {q.question_id: q for q in Question.objects.filter(question_id__in=qids)}

    # 组内分歧情况
    groups = (QuestionReview.objects.filter(question_id__in=qids)
              .values('question_id','suggested_answer','suggested_kp','suggested_primary','answer_wrong')
              .annotate(c=Count('id')))
    by_q = {}
    for g in groups:
        arr = by_q.setdefault(g['question_id'], [])
        arr.append({
            'suggested_answer': g['suggested_answer'] or '',
            'suggested_kp': g['suggested_kp'] or '',
            'suggested_primary': g['suggested_primary'] or '',
            'answer_wrong': bool(g['answer_wrong']),
            'count': int(g['c'])
        })
    out = []
    cons_th = _get_consensus_threshold()
    for t in totals[:limit]:
        qid = t['question_id']
        q = qmap.get(qid)
        arr = by_q.get(qid, [])
        arr.sort(key=lambda x: -x['count'])
        consensus = any(g['count'] >= cons_th for g in arr)
        conflict = (len(arr) >= 2 and not consensus)
        out.append({
            'question_id': qid,
            'type': q.question_type if q else '',
            'content': (q.content[:120] + '…') if (q and len(q.content) > 120) else (q.content if q else ''),
            'total_reviews': int(t['total']),
            'groups': arr,
            'consensus': consensus,
            'conflict': conflict,
        })
    return Response({'success': True, 'items': out})


@api_view(["GET"])  # 管理端：某题审查详情（按用户列出建议与解析）
def api_manage_review_detail(request):
    _, err = require_login(request, roles=['老师','管理员'])
    if err: return err
    qid = request.query_params.get('question_id')
    try:
        qid = int(qid)
    except Exception:
        return Response({'success': False, 'error_msg': 'question_id 参数错误'}, status=400)
    try:
        q = Question.objects.get(question_id=qid)
    except Question.DoesNotExist:
        return Response({'success': False, 'error_msg': '题目不存在'}, status=404)
    # 列出所有审查记录
    rows = (QuestionReview.objects
            .filter(question_id=qid)
            .select_related('user')
            .order_by('-updated_at'))
    items = []
    for r in rows:
        items.append({
            'user_id': r.user_id,
            'username': getattr(r.user, 'username', f'u{r.user_id}'),
            'suggested_answer': r.suggested_answer or '',
            'suggested_kp': r.suggested_kp or '',
            'suggested_primary': r.suggested_primary or '',
            'answer_wrong': bool(r.answer_wrong),
            'analysis': r.suggested_analysis or '',
            'updated_at': r.updated_at,
        })
    return Response({'success': True,
                     'question': {
                         'id': q.question_id,
                         'type': q.question_type,
                         'content': q.content,
                         'answer': q.answer or '',
                         'knowledge_points': q.knowledge_points or '',
                         'primary_knowledge': q.primary_knowledge or '',
                         'analysis': q.analysis or ''
                     },
                     'reviews': items})
