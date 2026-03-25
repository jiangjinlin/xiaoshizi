# 聚合导出各子模块的 API 视图，保持 app01.views 的兼容调用
from .public import (
    index,
    api_overview,
    api_exam_list,
    api_exam_select,
    api_question_import,
    api_score_query,
    api_score_word,
    api_score_excel,
    api_score_ppt,
    api_submit_exam,
    api_score_detail,
    api_register,
    api_q_comments,          # 题目评论列表（提交后可见）
    api_q_comments_create,   # 题目发表评论（提交后可见）
    api_q_comments_delete,   # 题目评论删除（本人/老师/管理员）
    api_q_comment_like,      # 新增：评论点赞
    api_q_comment_unlike,    # 新增：评论取消点赞
)
from .practice import (
    api_practice_options,
    api_practice_questions,
    api_practice_check,
    api_practice_stats,        # 新增：题型练习统计
    api_practice_mistakes,     # 新增：错题列表
)
from .auth_profile import (
    api_login,
    api_logout,
    api_profile_info,
    api_profile_save,
    api_profile_avatar,
    api_profile_bind,
)
from .face import (
    api_face_register,
    api_face_signin,
    api_face_status,
    api_face_supplement_submit,
    api_face_supplement_status,
    api_manage_face_supplements,
    api_manage_face_supplement_approve,
    api_manage_face_supplement_reject,
    api_face_eligibility,  # 新增：人脸审核资格查询
    api_face_profile,                 # 新增：用户人脸档案状态
    api_manage_face_setting,          # 新增：全局人脸开关获取
    api_manage_face_setting_save,     # 新增：全局人脸开关设置
    api_manage_face_reset,            # 新增：管理员重置用户人脸
)
from .manage import (
    api_manage_batch_list,
    api_manage_exam_list,
    api_manage_exam_detail,
    api_manage_exam_save,
    api_manage_exam_delete,
    api_manage_exam_publish,
    api_manage_question_list,
    api_manage_question_detail,
    api_manage_question_save,
    api_manage_question_delete,
    api_manage_question_export,
    api_manage_score_list,
    api_manage_score_delete,
    api_manage_student_list,
    api_manage_student_save,
    api_manage_student_delete,
    api_manage_exam_signins,
    api_manage_question_template,  # 新增导出：题目导入模板
    api_manage_question_bulk_delete,  # 新增聚合导出
    api_manage_question_bulk_mark_reviewed,  # 新增：批量标记审核
    api_manage_batch_stats,  # 新增：批次统计
    api_manage_batch_create,  # 新增：批次创建(自由组题)
    api_manage_batch_debug,  # 新增：批次调试
    api_manage_q_comments,   # 新增：评论管理列表
    api_manage_q_comment_delete, # 新增：评论删除
    api_manage_face_overview,  # 新增：全局人脸/VIP 概览
    api_manage_students_batch_degrade_vip,  # 新增批量降级 VIP
    api_manage_face_expiring,               # 新增人脸到期列表
    api_manage_review_queue,                # 新增：待审核题目队列
    api_manage_review_consensus,            # 新增：获取审查共识阈值
    api_manage_review_consensus_save,       # 新增：保存审查共识阈值
)
from .syllabus import (
    api_syllabus_options,
    api_syllabus_questions,
    api_syllabus_stats,        # 新增：知识点掌握度统计
    api_syllabus_presets,      # 新增：预置省份/专业与kp映射
    api_manage_syllabus_import_text,  # 新增：管理端一键导入（文本）
    api_manage_syllabus_list,  # 新增：列表
    api_manage_syllabus_save,  # 新增：保存
    api_manage_syllabus_delete,# 新增：删除
    api_manage_syllabus_clear, # 新增：清空
    api_manage_syllabus_export,      # 新增导出
    api_manage_syllabus_template,    # 新增模板（Markdown）
    api_manage_syllabus_template_excel, # 新增模板（Excel）
    api_manage_syllabus_import_excel,   # 新增Excel导入
    api_manage_syllabus_dedupe,      # 新增去重
    api_manage_syllabus_rename_kp,   # 新增大类重命名
    api_syllabus_selection,          # 新增：会话级考纲查询
    api_syllabus_selection_save,     # 新增：会话级考纲保存
)
# 新增：题目审查
from .review import (
    api_review_next,
    api_review_submit,
    api_review_rank,           # 新增：贡献榜
    api_manage_review_stats,   # 新增：管理端审查统计
    api_manage_review_detail,  # 新增：管理端审查详情
)
