import app01.views as views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic.base import RedirectView
from django.http import FileResponse, Http404
from pathlib import Path
from django.views.decorators.cache import never_cache

# 单文件静态兼容：优先从 STATICFILES_DIRS 查找 /static/logo.png，不存在则回退到项目根目录 logo.png

def static_logo(request):
    candidates = []
    try:
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            candidates.append(Path(d) / 'logo.png')
    except Exception:
        pass
    try:
        candidates.append(Path(settings.BASE_DIR) / 'logo.png')
    except Exception:
        pass
    for p in candidates:
        try:
            if p and p.exists():
                return FileResponse(open(p, 'rb'), content_type='image/png')
        except Exception:
            continue
    raise Http404('logo not found')

def spa_index(request):
    """最省事的前端托管：直接返回 my-front-end/dist/index.html（用于生产/本机部署）。"""
    dist_index = Path(settings.BASE_DIR).parent / 'my-front-end' / 'dist' / 'index.html'
    if not dist_index.exists():
        raise Http404('front-end dist/index.html not found. Please run `npm run build` in my-front-end.')
    return FileResponse(open(dist_index, 'rb'), content_type='text/html; charset=utf-8')


urlpatterns = [
    # 前端入口（SPA）：仅生产启用
    path('api', views.index, name='api_index_no_slash'),  # 新增：无斜杠版本，避免 301 重定向
    path('api/', views.index, name='api_index'),
    path('api/register', views.api_register, name='api_register'),
    path('api/exams', views.api_exam_list, name='api_exam_list'),
    path('api/exam-select', views.api_exam_select, name='api_exam_select'),
    path('api/question-import', views.api_question_import, name='api_question_import'),
    path('api/score-query', views.api_score_query, name='api_score_query'),
    path('api/score-word', views.api_score_word, name='api_score_word'),
    path('api/score-excel', views.api_score_excel, name='api_score_excel'),
    path('api/score-ppt', views.api_score_ppt, name='api_score_ppt'),
    path('api/submit-exam', views.api_submit_exam, name='api_submit_exam'),
    path('api/login', views.api_login, name='api_login'),
    path('api/logout', views.api_logout, name='api_logout'),
    path('api/overview', views.api_overview, name='api_overview'),
    path('api/score-detail', views.api_score_detail, name='api_score_detail'),

    # 人脸识别与补充
    path('api/face/register', views.api_face_register, name='api_face_register'),
    path('api/face/signin', views.api_face_signin, name='api_face_signin'),
    path('api/face/status', views.api_face_status, name='api_face_status'),
    path('api/face/supplement/submit', views.api_face_supplement_submit, name='api_face_supplement_submit'),
    path('api/face/supplement/status', views.api_face_supplement_status, name='api_face_supplement_status'),
    path('api/face/eligibility', views.api_face_eligibility, name='api_face_eligibility'),  # 新增：人脸审核资格查询
    path('api/face/profile', views.api_face_profile, name='api_face_profile'),

    # 个人主页
    path('api/profile/info', views.api_profile_info, name='api_profile_info'),
    path('api/profile/save', views.api_profile_save, name='api_profile_save'),
    path('api/profile/bind', views.api_profile_bind, name='api_profile_bind'),
    path('api/profile/avatar', views.api_profile_avatar, name='api_profile_avatar'),

    # 专项练习
    path('api/practice/options', views.api_practice_options, name='api_practice_options'),
    path('api/practice/questions', views.api_practice_questions, name='api_practice_questions'),
    path('api/practice/check', views.api_practice_check, name='api_practice_check'),
    path('api/practice/stats', views.api_practice_stats, name='api_practice_stats'),
    path('api/practice/mistakes', views.api_practice_mistakes, name='api_practice_mistakes'),

    # 管理端
    path('api/manage/batches', views.api_manage_batch_list, name='api_manage_batch_list'),
    path('api/manage/exams', views.api_manage_exam_list, name='api_manage_exam_list'),
    path('api/manage/exam/detail', views.api_manage_exam_detail, name='api_manage_exam_detail'),
    path('api/manage/exam/save', views.api_manage_exam_save, name='api_manage_exam_save'),
    path('api/manage/exam/delete', views.api_manage_exam_delete, name='api_manage_exam_delete'),
    path('api/manage/exam/publish', views.api_manage_exam_publish, name='api_manage_exam_publish'),

    path('api/manage/questions', views.api_manage_question_list, name='api_manage_question_list'),
    path('api/manage/question/detail', views.api_manage_question_detail, name='api_manage_question_detail'),
    path('api/manage/question/save', views.api_manage_question_save, name='api_manage_question_save'),
    path('api/manage/question/delete', views.api_manage_question_delete, name='api_manage_question_delete'),
    path('api/manage/question/export', views.api_manage_question_export, name='api_manage_question_export'),
    path('api/manage/question/template', views.api_manage_question_template, name='api_manage_question_template'),
    path('api/manage/question/bulk-delete', views.api_manage_question_bulk_delete, name='api_manage_question_bulk_delete'),
    path('api/manage/question/bulk-mark-reviewed', views.api_manage_question_bulk_mark_reviewed, name='api_manage_question_bulk_mark_reviewed'),

    path('api/manage/scores', views.api_manage_score_list, name='api_manage_score_list'),
    path('api/manage/score/delete', views.api_manage_score_delete, name='api_manage_score_delete'),

    path('api/manage/students', views.api_manage_student_list, name='api_manage_student_list'),
    path('api/manage/student/save', views.api_manage_student_save, name='api_manage_student_save'),
    path('api/manage/student/delete', views.api_manage_student_delete, name='api_manage_student_delete'),
    path('api/manage/students/batch-degrade-vip', views.api_manage_students_batch_degrade_vip, name='api_manage_students_batch_degrade_vip'),

    # 新增：考试签到情况
    path('api/manage/exam/signins', views.api_manage_exam_signins, name='api_manage_exam_signins'),

    # 新增：人脸补充审核
    path('api/manage/face/supplements', views.api_manage_face_supplements, name='api_manage_face_supplements'),
    path('api/manage/face/supplement/approve', views.api_manage_face_supplement_approve, name='api_manage_face_supplement_approve'),
    path('api/manage/face/supplement/reject', views.api_manage_face_supplement_reject, name='api_manage_face_supplement_reject'),

    # 考纲知识练习
    path('api/syllabus/options', views.api_syllabus_options, name='api_syllabus_options'),
    path('api/syllabus/questions', views.api_syllabus_questions, name='api_syllabus_questions'),
    path('api/syllabus/stats', views.api_syllabus_stats, name='api_syllabus_stats'),
    path('api/syllabus/selection', views.api_syllabus_selection, name='api_syllabus_selection'),
    path('api/syllabus/selection/save', views.api_syllabus_selection_save, name='api_syllabus_selection_save'),

    # 新增：考纲预置与导入
    path('api/syllabus/presets', views.api_syllabus_presets, name='api_syllabus_presets'),
    path('api/manage/syllabus/import-text', views.api_manage_syllabus_import_text, name='api_manage_syllabus_import_text'),

    # 新增：考纲管理（CRUD）
    path('api/manage/syllabus/list', views.api_manage_syllabus_list, name='api_manage_syllabus_list'),
    path('api/manage/syllabus/save', views.api_manage_syllabus_save, name='api_manage_syllabus_save'),
    path('api/manage/syllabus/delete', views.api_manage_syllabus_delete, name='api_manage_syllabus_delete'),
    path('api/manage/syllabus/clear', views.api_manage_syllabus_clear, name='api_manage_syllabus_clear'),
    path('api/manage/syllabus/export', views.api_manage_syllabus_export, name='api_manage_syllabus_export'),
    path('api/manage/syllabus/template', views.api_manage_syllabus_template, name='api_manage_syllabus_template'),
    path('api/manage/syllabus/template-excel', views.api_manage_syllabus_template_excel, name='api_manage_syllabus_template_excel'),
    path('api/manage/syllabus/import-excel', views.api_manage_syllabus_import_excel, name='api_manage_syllabus_import_excel'),
    path('api/manage/syllabus/dedupe', views.api_manage_syllabus_dedupe, name='api_manage_syllabus_dedupe'),
    path('api/manage/syllabus/rename-kp', views.api_manage_syllabus_rename_kp, name='api_manage_syllabus_rename_kp'),

    # 新增：批次统计
    path('api/manage/batch/stats', views.api_manage_batch_stats, name='api_manage_batch_stats'),
    # 新增：批次创建（自由组题）
    path('api/manage/batch/create', views.api_manage_batch_create, name='api_manage_batch_create'),

    # 新增：批次调试
    path('api/manage/batch/debug', views.api_manage_batch_debug, name='api_manage_batch_debug'),

    # 题目审查
    path('api/review/next', views.api_review_next, name='api_review_next'),
    path('api/review/submit', views.api_review_submit, name='api_review_submit'),
    path('api/review/rank', views.api_review_rank, name='api_review_rank'),
    path('api/manage/review/stats', views.api_manage_review_stats, name='api_manage_review_stats'),
    path('api/manage/review/detail', views.api_manage_review_detail, name='api_manage_review_detail'),
    path('api/manage/review/queue', views.api_manage_review_queue, name='api_manage_review_queue'),

    # 新增：审查共识阈值 获取/保存
    path('api/manage/review/consensus', views.api_manage_review_consensus, name='api_manage_review_consensus'),
    path('api/manage/review/consensus/save', views.api_manage_review_consensus_save, name='api_manage_review_consensus_save'),

    # 题目评论（提交后可见）
    path('api/q-comments', views.api_q_comments, name='api_q_comments'),
    path('api/q-comments/create', views.api_q_comments_create, name='api_q_comments_create'),
    path('api/q-comments/delete', views.api_q_comments_delete, name='api_q_comments_delete'),
    path('api/q-comment/like', views.api_q_comment_like, name='api_q_comment_like'),
    path('api/q-comment/unlike', views.api_q_comment_unlike, name='api_q_comment_unlike'),

    # 教师：评论管理
    path('api/manage/q-comments', views.api_manage_q_comments, name='api_manage_q_comments'),
    path('api/manage/q-comment/delete', views.api_manage_q_comment_delete, name='api_manage_q_comment_delete'),
    path('api/manage/face/setting', views.api_manage_face_setting, name='api_manage_face_setting'),
    path('api/manage/face/setting/save', views.api_manage_face_setting_save, name='api_manage_face_setting_save'),

    # 新增：人脸数据概览
    path('api/manage/face/overview', views.api_manage_face_overview, name='api_manage_face_overview'),
    path('api/manage/face/expiring', views.api_manage_face_expiring, name='api_manage_face_expiring'),

    # Logo 兼容路径：将 /logo.png 重定向到 /static/logo.png
    path('logo.png', RedirectView.as_view(url='/static/logo.png', permanent=True)),
    # 提供 /static/logo.png：优先取 app 静态目录，缺省回退到仓库根 logo.png
    path('static/logo.png', static_logo, name='static_logo'),
    # 兼容路径：/api/static/logo.png（防止 baseURL 含路径时产生双重前缀）
    path('api/static/logo.png', static_logo, name='api_static_logo'),
]

# 仅上线( DEBUG=0 )时接管根路径 '/'，本地开发( DEBUG=1 )不注册该路由，避免影响 Vite dev server/本地访问
if not settings.DEBUG:
    urlpatterns.insert(0, path('', never_cache(spa_index), name='index'))

# 生产最省事：即使 DEBUG=0 也直接由 Django 托管 media（不推荐高并发，但最简单）
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
