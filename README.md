# 在线考试系统（Django + DRF + Vue）

本项目是一个基于 **Django + Django REST Framework（DRF）** 的在线考试系统，支持：

- 客观题自动判分
- Office 操作题评分（Word / Excel / PPT）
- 人脸识别签到（本地 aHash / 百度云）
- 管理端：考试发布、题库维护、成绩与签到管理

前端为 **Vite + Vue 3**（位于 `my-front-end/`）。

---

## 目录结构（与当前仓库一致）

- `Django/`：后端项目根
  - `manage.py`
  - `app01/`：主应用
    - `api/`：按领域拆分的接口模块
      - `public.py`：公共/考试/成绩/导题等
      - `practice.py`：专项练习
      - `auth_profile.py`：登录/登出/资料/头像
      - `face.py`：人脸注册/签到/补充审核
      - `manage.py`：管理端（考试/题库/成绩/学生/签到）
      - `review.py`：错题/复习、排行榜等（如：review 相关能力）
      - `syllabus.py`：大纲/章节（与前端 SyllabusPicker 对应）
      - `utils.py`：通用工具
      - `__init__.py`：聚合导出（供 `app01.views` 使用）
    - `views.py`：仅聚合导出（保持对 `Django/urls.py` 兼容）
    - `scoring/`：Office 操作题评分（Word/Excel/PPT）
    - `models.py`：数据模型
    - `middleware.py`、`signals.py` 等
    - `static/`：静态资源（含 `static/template/` 操作题模板）
    - `templates/`：模板
  - `Django/`：项目配置
    - `settings.py` / `urls.py` / `wsgi.py` / `asgi.py`
  - `media/`：上传目录（头像、人脸、人脸待审核等）
- `my-front-end/`：前端（Vite + Vue 3）

> 说明：后端路由仍在 `Django/Django/urls.py` 中统一配置，并继续引用 `app01.views`，而 `app01.views` 再聚合 `app01/api/*` 下各模块的函数，因此前端调用路径一般无需调整。

---

## 环境要求

- Python 3.10+（你当前环境里能看到 `cpython-313`，表示也支持 Python 3.13）
- Node.js 18+（前端）
- Windows / macOS / Linux 均可（本 README 命令以 Windows `cmd.exe` 为主）

---

## 快速开始（后端）

### 1）安装依赖

当前仓库 **未提供 `requirements.txt`**（以实际文件为准），可以先按项目常用依赖安装：
```bat
pip install -r requirements.txt
```

```bat
pip install django djangorestframework pillow openpyxl
```

如果你后续补上了 `requirements.txt`，优先使用：

```bat
pip install -r requirements.txt
```

### 2）迁移数据库并启动

```bat
cd Django
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 3）后端连通性检查

浏览器打开：

- http://localhost:8000/api/

---

## 快速开始（前端）

```bat
cd my-front-end
npm install
npm run dev
```

启动后按终端提示访问地址（一般为 http://localhost:5173）。

---

## 前后端联调说明

- 前端接口封装位于：`my-front-end/src/api/`
- 若前端通过代理转发到 Django，请检查：`my-front-end/vite.config.js`
- 若不使用代理，请确保前端请求的 baseURL 指向 `http://localhost:8000/`（具体以 `src/api/http.js` 实现为准）

---

## 人脸识别配置（可选）

在 `Django/Django/settings.py` 中支持通过环境变量或直接配置（字段名以你项目现有实现为准）：

```python
import os

BAIDU_FACE = {
  'APP_ID': os.getenv('BAIDU_APP_ID', ''),
  'API_KEY': os.getenv('BAIDU_API_KEY', ''),
  'SECRET_KEY': os.getenv('BAIDU_SECRET', ''),
  'GROUP_ID': os.getenv('BAIDU_GROUP', 'exam_users'),
  'THRESHOLD': os.getenv('BAIDU_THRESHOLD', '80'),
}
LOCAL_FACE = {
  'THRESHOLD': os.getenv('LOCAL_FACE_THRESHOLD', '85'),
}
FACE_SIGNIN_TTL_MINUTES = int(os.getenv('FACE_TTL', '120'))
```

- 开启云端识别：`APP_ID / API_KEY / SECRET_KEY` 需有效；否则走本地 aHash。
- 本地 aHash 门限默认 85，可按摄像头清晰度与光照条件调整。

---

## API 概览（按模块）

以下为主要 API 分组（仅列出常用路径，实际以 `urls.py` 为准）：

### 公共 / 考试（`app01/api/public.py`）

- `GET /api/`：健康检查
- `GET /api/overview`：首页概览
- `POST /api/register`：用户注册
- `GET /api/exams`：当前有效考试及题目
- `GET /api/exam-select`：已发布考试列表
- `POST /api/submit-exam`：提交考试
- `GET /api/score-detail`：成绩详情
- `GET /api/score-query`：我的成绩列表
- `POST /api/question-import`：批量导题（Excel）

### 练习（`app01/api/practice.py`）

- `GET /api/practice/options`：练习可选项
- `GET/POST /api/practice/questions`：抽题
- `POST /api/practice/check`：判题

### 认证 / 资料（`app01/api/auth_profile.py`）

- `POST /api/login`、`POST /api/logout`
- `GET /api/profile/info`
- `POST /api/profile/save`
- `POST /api/profile/avatar`

### 人脸（`app01/api/face.py`）

- `POST /api/face/register`：人脸注册
- `POST /api/face/signin`：人脸签到（`mode=local/cloud/auto`）
- `GET /api/face/status`：签到状态
- `POST /api/face/supplement/submit`：补充提交
- `GET /api/face/supplement/status`：补充记录查询
- `GET /api/manage/face/supplements`：管理端审核列表
- `POST /api/manage/face/supplement/approve|reject`：审核

### 复习 / 错题 / 排名（`app01/api/review.py`）

- 与 `review` 页面相关的接口（如错题列表、复习数据、排行榜等）

### 大纲 / 章节（`app01/api/syllabus.py`）

- 与前端章节选择、题目范围过滤相关接口

### 管理端（`app01/api/manage.py`）

- `GET /api/manage/exams`、`/exam/detail`、`/questions`、`/scores`、`/students`
- `POST /api/manage/exam/save|delete|publish`
- `POST /api/manage/question/save|delete`
- `GET /api/manage/question/export`
- `POST /api/manage/score/delete`
- `POST /api/manage/student/save|delete`
- `GET /api/manage/exam/signins`

---

## 常见问题（FAQ）

1. **启动后访问 `/api/` 404？**
   - 先确认你启动的是 `Django/manage.py`（路径：`Django\manage.py`），并检查 `Django/Django/urls.py` 是否已包含 `/api/` 前缀路由。

2. **人脸签到一直失败/误判？**
   - 优先调低/调高 `LOCAL_FACE_THRESHOLD`，并使用光照更稳定的环境。

3. **Office 操作题评分不生效？**
   - 评分逻辑在 `Django/app01/scoring/`，同时依赖 `static/template/` 下的模板文件；请确认模板完整且后端能读到。

---

## 开发建议

- 新增接口按领域放入 `app01/api/` 对应模块；公用函数放入 `app01/api/utils.py`。
- 若要扩展操作题类型，请在 `app01/scoring/` 新增模块，并在提交/评分分支中接入。
