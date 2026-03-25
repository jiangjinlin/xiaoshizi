import { http } from './http'

// Auth
export const apiIndex = () => http.get('/api/')
export const apiLogin = data => http.post('/api/login', data)
export const apiRegister = data => http.post('/api/register', data)
export const apiLogout = () => http.post('/api/logout')

// 考试
export const apiExamList = () => http.get('/api/exams')
// 改为 GET 以适配后端 path('api/exam-select', ...) 定义
export const apiExamSelect = (params = {}) => http.get('/api/exam-select', { params })
export const apiSubmitExam = data => http.post('/api/submit-exam', data)

// 人脸识别（支持按考试）
export const apiFaceRegister = (image_base64, username) => http.post('/api/face/register', { image_base64, username })
export const apiFaceSignin = (image_base64, exam_id, mode = 'auto') => http.post('/api/face/signin', { image_base64, exam_id, mode })
export const apiFaceStatus = (params={}) => http.get('/api/face/status', { params })
// 人脸补充
export const apiFaceSupplementSubmit = (image_base64) => http.post('/api/face/supplement/submit', { image_base64 })
export const apiFaceSupplementStatus = () => http.get('/api/face/supplement/status')
// 管理端人脸补充审核
export const apiManageFaceSupplements = (params={}) => http.get('/api/manage/face/supplements', { params })
export const apiManageFaceSupplementApprove = (id) => http.post('/api/manage/face/supplement/approve', { id })
export const apiManageFaceSupplementReject = (id, reason='') => http.post('/api/manage/face/supplement/reject', { id, reason })
// 人脸识别资格
export const apiFaceEligibility = () => http.get('/api/face/eligibility')

// 人脸识别 - 个人信息
export const apiFaceProfile = () => http.get('/api/face/profile')

// 人脸识别 - 全局设置
export const apiManageFaceSetting = () => http.get('/api/manage/face/setting')
export const apiManageFaceSettingSave = (face_required) => http.post('/api/manage/face/setting/save', { face_required })
export const apiManageFaceReset = (payload) => http.post('/api/manage/face/reset', payload)

// 题目导入/导出
export const apiQuestionImport = formData => http.post('/api/question-import', formData, { headers:{'Content-Type':'multipart/form-data'} })

export const apiScoreQuery = (params={}) => http.get('/api/score-query', { params })
export const apiScoreWord = data => http.post('/api/score-word', data)
export const apiOverview = () => http.get('/api/overview')
export const apiScoreDetail = (record_id) => http.get('/api/score-detail', { params:{ record_id } })

// 专项练习
export const apiPracticeOptions = (params={}) => http.get('/api/practice/options', { params })
export const apiPracticeQuestions = (params={}) => http.get('/api/practice/questions', { params })
export const apiPracticeCheck = (payload) => http.post('/api/practice/check', payload)
// 新增：练习统计 & 错题
export const apiPracticeStats = () => http.get('/api/practice/stats')
export const apiPracticeMistakes = (params={}) => http.get('/api/practice/mistakes', { params })

// 知识点/考纲练习
export const apiSyllabusOptions = () => http.get('/api/syllabus/options')
export const apiSyllabusQuestions = (params={}) => http.get('/api/syllabus/questions', { params })
export const apiSyllabusStats = (params={}) => http.get('/api/syllabus/stats', { params })
// 全局（会话）考纲选择
export const apiSyllabusSelection = () => http.get('/api/syllabus/selection')
export const apiSyllabusSelectionSave = (province='', major='') => http.post('/api/syllabus/selection/save', { province, major })
// 考纲预置（省份/专业与kp映射）
export const apiSyllabusPresets = (params = {}) => http.get('/api/syllabus/presets', { params })
// 管理端：考纲一键导入（文本）
export const apiManageSyllabusImportText = (payload) => http.post('/api/manage/syllabus/import-text', payload)

// 管理端：批次 / 考试
export const apiManageBatchList = () => http.get('/api/manage/batches')
export const apiManageExamList = () => http.get('/api/manage/exams')
export const apiManageExamDetail = id => http.get('/api/manage/exam/detail', { params:{ id } })
export const apiManageExamSave = payload => http.post('/api/manage/exam/save', payload)
export const apiManageExamDelete = id => http.post('/api/manage/exam/delete', { id })
export const apiManageExamPublish = (id, is_published) => http.post('/api/manage/exam/publish', { id, is_published })
export const apiManageExamSignins = (params={}) => http.get('/api/manage/exam/signins', { params })

// 管理端：题库
export const apiManageQuestionList = (params={}) => http.get('/api/manage/questions', { params })
export const apiManageQuestionDetail = id => http.get('/api/manage/question/detail', { params:{ id } })
export const apiManageQuestionSave = payload => http.post('/api/manage/question/save', payload)
export const apiManageQuestionDelete = id => http.post('/api/manage/question/delete', { id })
export const apiManageQuestionExport = (params={}) => http.get('/api/manage/question/export', { params, responseType: 'blob' })
export const apiManageQuestionBulkDelete = (ids=[]) => http.post('/api/manage/question/bulk-delete', { ids })
export const apiManageQuestionTemplate = () => http.get('/api/manage/question/template', { responseType: 'blob' })
export const apiManageQuestionBulkMarkReviewed = (ids=[], reviewed=true) => http.post('/api/manage/question/bulk-mark-reviewed', { ids, reviewed })

// 新增：管理端 批次相关接口
export const apiManageBatchStats = (params={}) => http.get('/api/manage/batch/stats', { params })
export const apiManageBatchCreate = (payload) => http.post('/api/manage/batch/create', payload)

// 管理端：成绩
export const apiManageScoreList = (params={}) => http.get('/api/manage/scores', { params })
export const apiManageScoreDelete = id => http.post('/api/manage/score/delete', { id })

// 管理端：学生
export const apiManageStudentList = (params={}) => http.get('/api/manage/students', { params })
export const apiManageStudentSave = payload => http.post('/api/manage/student/save', payload)
export const apiManageStudentDelete = id => http.post('/api/manage/student/delete', { id })
export const apiManageStudentsBatchDegradeVip = (user_ids=[]) => http.post('/api/manage/students/batch-degrade-vip', { user_ids })

// 个人主页
export const apiProfileInfo = () => http.get('/api/profile/info')
export const apiProfileSave = (payload) => http.post('/api/profile/save', payload)
export const apiProfileBind = (payload) => http.post('/api/profile/bind', payload)
export const apiProfileAvatar = (formData) => http.post('/api/profile/avatar', formData, { headers:{ 'Content-Type': 'multipart/form-data' } })

// 题目审查
export const apiReviewNext = (params={}) => http.get('/api/review/next', { params })
export const apiReviewSubmit = (payload) => http.post('/api/review/submit', payload)
export const apiReviewRank = () => http.get('/api/review/rank')
export const apiManageReviewStats = (params={}) => http.get('/api/manage/review/stats', { params })
export const apiManageReviewDetail = (question_id) => http.get('/api/manage/review/detail', { params: { question_id } })
export const apiManageReviewQueue = (params={}) => http.get('/api/manage/review/queue', { params })
// 新增：审查共识阈值（老师/管理员）
export const apiManageReviewConsensus = () => http.get('/api/manage/review/consensus')
export const apiManageReviewConsensusSave = (threshold) => http.post('/api/manage/review/consensus/save', { threshold })

// 新增：题目评论（需已作答）
export const apiQComments = (question_id) => http.get('/api/q-comments', { params: { question_id } })
export const apiQCommentsCreate = (payload) => http.post('/api/q-comments/create', payload)
export const apiQCommentsDelete = (id) => http.post('/api/q-comments/delete', { id })
export const apiQCommentLike = (id) => http.post('/api/q-comment/like', { id })
export const apiQCommentUnlike = (id) => http.post('/api/q-comment/unlike', { id })

// 教师：评论管理
export const apiManageQComments = (params={}) => http.get('/api/manage/q-comments', { params })
export const apiManageQCommentDelete = (id) => http.post('/api/manage/q-comment/delete', { id })

// 管理端：考纲管理（CRUD）
export const apiManageSyllabusList = (params={}) => http.get('/api/manage/syllabus/list', { params })
export const apiManageSyllabusSave = (payload) => http.post('/api/manage/syllabus/save', payload)
export const apiManageSyllabusDelete = (payload) => http.post('/api/manage/syllabus/delete', payload)
export const apiManageSyllabusClear = (payload) => http.post('/api/manage/syllabus/clear', payload)
export const apiManageSyllabusExport = (params={}) => http.get('/api/manage/syllabus/export', { params, responseType: 'blob' })
export const apiManageSyllabusTemplate = () => http.get('/api/manage/syllabus/template', { responseType: 'blob' })
export const apiManageSyllabusDedupe = (payload) => http.post('/api/manage/syllabus/dedupe', payload)
export const apiManageSyllabusRenameKp = (payload) => http.post('/api/manage/syllabus/rename-kp', payload)
export const apiManageSyllabusTemplateExcel = () => http.get('/api/manage/syllabus/template-excel', { responseType: 'blob' })
export const apiManageSyllabusImportExcel = (formData) => http.post('/api/manage/syllabus/import-excel', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const apiManageFaceOverview = () => http.get('/api/manage/face/overview')
export const apiManageFaceExpiring = (params={}) => http.get('/api/manage/face/expiring', { params })
