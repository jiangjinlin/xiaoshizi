"""
Django 数据库模型定义（app01.models）
- 覆盖用户、题目、考试、组卷、考试记录、答题记录、操作题评分、人脸档案与签到记录等核心表。
- 仅添加中文文档注释与说明，不更改任何字段/索引定义，避免产生迁移。
- 如需查看字段用途与约束，可阅读各模型类的 docstring 与行内注释。
"""

from django.db import models
import os
import uuid
from datetime import datetime

# 头像保存路径：按日期+用户ID+短UUID 命名，保留扩展名，默认 .jpg
# e.g. avatars/20250913/u12_ab12cd34ef.jpg

def user_avatar_upload_to(instance, filename):
    """头像文件保存路径生成器
    命名规则：avatars/YYYYMMDD/u<user_id>_<短UUID>.<ext>
    仅允许常见图片扩展名（.jpg/.jpeg/.png/.gif/.webp），否则强制改为 .jpg。
    """
    # 安全扩展名白名单
    allowed_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ext = os.path.splitext(str(filename or ''))[1].lower()
    if ext not in allowed_exts:
        ext = '.jpg'
    uid = getattr(instance, 'user_id', None) or 'new'
    date = datetime.now().strftime('%Y%m%d')
    return f"avatars/{date}/u{uid}_{uuid.uuid4().hex[:10]}{ext}"

# 新增：本地人脸图片保存路径

def user_face_upload_to(instance, filename):
    """人脸图片保存路径生成器
    命名规则：faces/YYYYMMDD/u<user_id>_<短UUID>.<ext>
    仅允许 .jpg/.jpeg/.png/.webp，其他扩展名强制改为 .jpg。
    """
    allowed_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    ext = os.path.splitext(str(filename or ''))[1].lower()
    if ext not in allowed_exts:
        ext = '.jpg'
    uid = getattr(getattr(instance, 'user', None), 'user_id', 'new')
    date = datetime.now().strftime('%Y%m%d')
    return f"faces/{date}/u{uid}_{uuid.uuid4().hex[:10]}{ext}"


class User(models.Model):
    """用户表（students/teachers/admins）
    字段：
      - user_id: 自增主键
      - username: 登录名（业务层保证唯一）
      - password: 明文存储示例，生产应加密（如 PBKDF2/BCrypt）
      - role: 角色（学生/老师/管理员）
      - fingerprint: 预留字段，已弃用；现统一使用人脸
      - department: 教师部门；学生/管理员可留空
      - classroom: 学生班级；老师/管理员可留空
      - nickname/email/phone/student_no: 扩展资料
      - avatar: 头像（存储于 MEDIA_ROOT/avatars/...）
    说明：
      - 业务上可对 username 建立唯一性约束；当前通过逻辑校验保证不重复。
    """
    user_id = models.AutoField(primary_key=True)  # 用户ID，自增主键
    username = models.CharField(max_length=50)  # 用户名
    password = models.CharField(max_length=100)  # 加密存储的密码
    role = models.CharField(max_length=10)  # 角色（学生/教师/管理员）
    fingerprint = models.BinaryField(null=True, blank=True)  # 指纹数据，可选
    department = models.CharField(max_length=50)  # 教师部门
    classroom = models.CharField(max_length=50)
    # 新增扩展资料
    nickname = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    student_no = models.CharField(max_length=50, blank=True, default='')
    avatar = models.ImageField(upload_to=user_avatar_upload_to, blank=True, null=True)
    vip_expires_at = models.DateTimeField(null=True, blank=True, help_text='VIP 到期时间（到期自动降级为学生）')  # 新增：VIP 到期

    objects = models.Manager()  # 显式默认管理器，便于类型检查

    class Meta:
        db_table = 'users'  # 替换为实际的数据库表名

    def __str__(self):
        return self.username

# 新增：本地人脸档案
class FaceProfile(models.Model):
    """用户人脸档案表
    用途：保存用户人脸图片与本地相似度特征（vector）以支持离线识别。
    字段：
      - user: 一对一关联到 User
      - image: 人脸图（MEDIA_ROOT/faces/...）
      - vector: 本地特征向量或哈希字符串（实现可替换）
      - created_at/updated_at: 记录创建与更新时间
    索引：user（便于按用户检索）
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='face_profile')
    image = models.ImageField(upload_to=user_face_upload_to, blank=True, null=True)
    vector = models.TextField(blank=True, default='')  # 逗号分隔的浮点特征
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='人脸有效期（审核通过起1个月，到期需重新审核）')  # 新增：到期删除

    objects = models.Manager()

    class Meta:
        db_table = 'face_profiles'
        indexes = [models.Index(fields=['user'])]

class Question(models.Model):
    """题库表
    字段：
      - question_id: 自增主键
      - question_type: 题型（单选/多选/判断/Office操作/操作）
      - A/B/C/D_answer: 选项文本
      - content: 题干
      - answer: 标准答案
      - score: 本题分值(难度)
      - batch: 所属批次（允许为空，便于后续由老师分配）
      - analysis: 解析
      - knowledge_points: 考纲大类
      - primary_knowledge: 一级知识点（考纲大类下级）
      - reviewed: 是否审核通过（默认False）
    """
    question_id = models.AutoField(primary_key=True)  # 题目ID，自增主键
    question_type = models.CharField(max_length=20)  # 题目类型（单选/多选/判断/Office操作）
    A_answer = models.TextField(null=True, blank=True)  # 选项A
    B_answer = models.TextField(null=True, blank=True)  # 选项B
    C_answer = models.TextField(null=True, blank=True)  # 选项C
    D_answer = models.TextField(null=True, blank=True)  # 选项D
    content = models.TextField()  # 题目内容
    answer = models.TextField()  # 答案
    score = models.IntegerField()  # 难度等级（1-5）
    batch = models.IntegerField(null=True, blank=True)  # 所属批次（允许为空）
    analysis = models.TextField(null=True, blank=True)  # 题目解析
    knowledge_points = models.CharField(max_length=255, blank=True, default='')  # 新增：考纲大类
    primary_knowledge = models.CharField(max_length=100, blank=True, default='')  # 新增：一级知识点
    reviewed = models.BooleanField(default=False)  # 新增：是否审核通过
    objects = models.Manager()

    class Meta:
        db_table = 'questions'


class Exam(models.Model):
    """考试计划表
    字段：
      - exam_id: 自增主键
      - title: 考试标题
      - start_time/end_time: 开始/结束时间窗口
      - duration: 时长（分钟）
      - is_published: 是否发布（仅发布后对学生可见）
    """
    exam_id = models.AutoField(primary_key=True)  # 考试ID，自增主键
    title = models.CharField(max_length=100)  # 考试标题
    start_time = models.DateTimeField()  # 考试开始时间
    end_time = models.DateTimeField()  # 考试结束时间
    duration = models.IntegerField()  # 考试时长（分钟）
    is_published = models.BooleanField(default=False)  # 是否发布
    objects = models.Manager()

    class Meta:
        db_table = 'exams'

class ExamQuestion(models.Model):
    """组卷表（考试-批次 多对多）
    说明：同一考试与同一批次的组合唯一（unique_together=(exam,batch)）。
    """
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)  # 考试ID，外键
    batch  = models.IntegerField()  # 批次
    objects = models.Manager()

    class Meta:
        db_table = 'exam_questions'
        unique_together = (('exam', 'batch'),)

class ExamRecord(models.Model):
    """考试成绩记录表
    字段：
      - record_id: 自增主键
      - user/exam: 外键
      - score: 得分（含客观题与操作题总分）
      - start_time/end_time: 作答开始/结束时间
      - submit_time: 提交时间
    """
    record_id = models.AutoField(primary_key=True)  # 考试记录ID，自增主键
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 用户ID，外键
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)  # 考试ID，外键
    score = models.FloatField()  # 考试成绩
    start_time = models.DateTimeField()  # 开始时间
    end_time = models.DateTimeField()  # 结束时间
    submit_time = models.DateTimeField(null=True, blank=True)  # 新增：提交时间
    objects = models.Manager()

    class Meta:
        db_table = 'exam_records'

class AnswerRecord(models.Model):
    """客观题作答明细表
    字段：
      - answer_id: 自增主键
      - record: 所属考试记录
      - question: 题目
      - user_answer: 用户答案（多选可保存如 ["A","C"] 或 "AC" 的字符串形式）
      - is_correct: 是否正确
    """
    answer_id = models.AutoField(primary_key=True)  # 答题记录ID，自增主键
    record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE)  # 考试记录ID，外键
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  # 题目ID，外键
    user_answer = models.TextField()  # 学生答案
    is_correct = models.BooleanField()  # 是否正确
    objects = models.Manager()


    class Meta:
        db_table = 'answer_records'


class OperationDetail(models.Model):
    """操作题评分明细（长期保存用于统计）。
    由提交接口在评分后写入；删除 ExamRecord 时级联删除。
    字段：
      - record: 考试记录
      - question: 操作题题目
      - score/total: 得分/题目配分（score 按评分结果按比例缩放到 total）
      - msg: 评分说明（命中项/未命中项等）
      - file_name: 用户提交的文件名
      - created_at: 创建时间
    索引：record, question
    """
    id = models.AutoField(primary_key=True)
    record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE, related_name='operation_details')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    score = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)
    msg = models.TextField(null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'operation_details'
        indexes = [
            models.Index(fields=['record']),
            models.Index(fields=['question']),
        ]

# 新增：考试人脸签到记录
class ExamSignIn(models.Model):
    """考试签到记录表
    用途：记录学生在某场考试的人脸签到结果与方式（本地/百度）。
    字段：
      - exam/user: 外键
      - success: 是否签到通过
      - method: 识别方式（local/baidu/空）
      - score: 相似度得分（本地哈希或云端分数）
      - reason: 失败原因（异常信息/校验失败等）
      - created_at: 记录时间
    索引：exam、user 以及 (exam,user,created_at) 复合索引（便于取最近一次）
    """
    id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    success = models.BooleanField(default=False)
    method = models.CharField(max_length=20, blank=True, default='')  # local/baidu
    score = models.FloatField(null=True, blank=True)  # 相似度分数
    reason = models.TextField(blank=True, default='')  # 失败原因/错误信息
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'exam_signins'
        indexes = [
            models.Index(fields=['exam']),
            models.Index(fields=['user']),
            models.Index(fields=['exam', 'user', 'created_at']),
        ]

class PracticeAnswer(models.Model):
    """练习答题统计表（不区分考试），用于专项/考纲练习差异化分析。
    每题每用户一条累计记录：总次数/正确次数/最近是否正确/最后作答时间。
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    total_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    last_is_correct = models.BooleanField(default=False)
    last_answer_time = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    class Meta:
        db_table = 'practice_answers'
        unique_together = (('user','question'),)
        indexes = [models.Index(fields=['user']), models.Index(fields=['question'])]


# 新增：题目审查记录
class QuestionReview(models.Model):
    """学生对题目的审查/建议记录。
    每个用户对同一题目最多一条记录（可覆盖更新）。
    字段：
      - user/question: 关联
      - suggested_answer: 建议标准答案（单选/判断为单字母，多选为按字母排序去重后的组合，如 "AC"）
      - suggested_kp: 建议考纲大类（单个值）
      - suggested_primary: 建议一级知识点
      - suggested_analysis: 建议解析
      - answer_wrong: 是否认为当前答案有误
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    suggested_answer = models.CharField(max_length=20, blank=True, default='')
    suggested_kp = models.CharField(max_length=255, blank=True, default='')
    suggested_primary = models.CharField(max_length=100, blank=True, default='')
    suggested_analysis = models.TextField(blank=True, default='')
    answer_wrong = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'question_reviews'
        unique_together = (('user','question'),)
        indexes = [models.Index(fields=['question']), models.Index(fields=['user'])]


# 新增：题目评论区（按题目ID）
class QuestionComment(models.Model):
    """题目级别的评论。
    字段：用户、题目、内容、时间。
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'question_comments'
        indexes = [
            models.Index(fields=['question']),
            models.Index(fields=['user']),
        ]

# 新增：题目评论点赞
class QuestionCommentLike(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(QuestionComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'question_comment_likes'
        unique_together = (('comment','user'),)
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['user']),
        ]

# 新增：考纲条目（教师导入）
class SyllabusItem(models.Model):
    """考纲条目（教师导入）
    用于按 省份/专业 存储：考纲大类(kp) 与 一级知识点(primary)。
    """
    id = models.AutoField(primary_key=True)
    province = models.CharField(max_length=50)
    major = models.CharField(max_length=50)
    kp = models.CharField(max_length=255)  # 考纲大类
    primary = models.CharField(max_length=255)  # 一级知识点内容
    objects = models.Manager()

    class Meta:
        db_table = 'syllabus_items'
        indexes = [
            models.Index(fields=['province','major']),
            models.Index(fields=['kp'])
        ]
        unique_together = (('province','major','kp','primary'),)

# 新增：全局配置表
class GlobalSetting(models.Model):
    """简单的全局配置表（key/value）。用于存储：
    - FACE_REQUIRED: '1' 开启访问需人脸验证
    未来可扩展更多键。
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'global_settings'
