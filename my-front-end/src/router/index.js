import {createRouter, createWebHashHistory} from "vue-router";
import Login from "../view/login.vue";
import Index from "../view/index.vue";
import Student from "../view/student.vue";
import Teacher from "../view/teacher.vue";
import Admin from "../view/admin.vue";
import Exam from "../view/exam.vue";
import Register from "../view/register.vue";
import { apiLogout } from "../api/index";
import ScoreQuery from "../view/score_query.vue";
import ExamManage from "../view/manage/ExamManage.vue";
import ExamForm from "../view/manage/ExamForm.vue";
import ManageQuestion from "../view/manage/ManageQuestion.vue";
import QuestionForm from "../view/manage/QuestionForm.vue";
import ScoreManage from "../view/manage/ScoreManage.vue";
import StudentManage from "../view/manage/StudentManage.vue";
import PracticeSetup from "../view/practice_setup.vue";
import practice from "../view/practice.vue";
import ScoreDetail from "../view/score_detail.vue";
import Profile from "../view/profile.vue";
import Signin from "../view/signin.vue";
import SigninsManage from "../view/manage/SigninsManage.vue";
import FaceSupplementsManage from "../view/manage/FaceSupplementsManage.vue";
import ExamSelect from "../view/exam_select.vue";
import SyllabusSetup from "../view/syllabus_setup.vue";
import SyllabusDo from "../view/syllabus_do.vue";
import SyllabusStats from "../view/syllabus_stats.vue";
import PracticeStats from "../view/practice_stats.vue";
import PracticeMistakes from "../view/practice_mistakes.vue";
import QuestionAdvanced from "../view/manage/QuestionAdvanced.vue";
import Review from "../view/review.vue";
import ReviewRank from "../view/review_rank.vue";
import ReviewStatsManage from "../view/manage/ReviewStats.vue";
import ReviewDetailManage from "../view/manage/ReviewDetail.vue";
import QCommentsManage from "../view/manage/QCommentsManage.vue";
import SyllabusManage from "../view/manage/SyllabusManage.vue";
import Contact from "../view/contact.vue";
import FaceExpiringManage from '../view/manage/FaceExpiringManage.vue';
import ReviewQueue from "../view/manage/ReviewQueue.vue";


const routes = [
    {
        path: "/",
        name: 'home',
        component: Index,
    }
    ,
    {
        path: "/login",
        name: 'login',
        component: Login,
    }
    ,
    {
        path: "/student",
        name: 'studentHome',
        component: Student,
        meta: { allowedRoles: ['学生','VIP'] }
    }
    ,
    {
        path: "/teacher",
        name: 'teacherHome',
        component: Teacher,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/admin",
        name: 'adminHome',
        component: Admin,
        meta: { allowedRoles: ['管理员'] }
    }
    ,
    {
        path: "/exam",
        name: 'exam',
        component: Exam,
    }
    ,
    {
        path: "/signin",
        name: 'signin',
        component: Signin,
    }
    ,
    {
        path: "/exam_select",
        name: 'examSelect',
        component: ExamSelect,
    }
    ,
    {
        path: "/register",
        name: 'register',
        component: Register,
    }
    ,
    {
        path: "/logout",
        component: () => apiLogout().then(() => {
            try { localStorage.removeItem('global_syllabus') } catch {}
            localStorage.removeItem('user_id');
            localStorage.removeItem('role');
            router.push('/login');
        }),
    }
    ,
    {
        path: "/score_query",
        component: ScoreQuery,
        meta: { allowedRoles: ['学生','VIP','老师','管理员'] }
    }
    ,
    {
        path: "/score_detail/:id",
        component: ScoreDetail,
        meta: { allowedRoles: ['学生','VIP','老师','管理员'] }
    }
    ,
    {
        path: "/profile",
        name: 'profile',
        component: Profile,
        meta: { allowedRoles: ['学生','VIP','老师','管理员'] }
    }
    ,
    // 专项练习
    {
        path: "/practice",
        redirect: "/practice/setup",
        meta: { allowedRoles: ['学生','VIP'] }
    }
    ,
    {
        path: "/practice/setup",
        name: 'practiceSetup',
        component: PracticeSetup,
        meta: { allowedRoles: ['学生','VIP'] }
    }
    ,
    {
        path: "/practice/do",
        name: 'practiceDo',
        component: practice,
        meta: { allowedRoles: ['学生','VIP'] }
    }
    ,
    // 专项练习统计 & 错题
    { path: "/practice/stats", name: 'practiceStats', component: PracticeStats, meta: { allowedRoles: ['学生','VIP'] } },
    { path: "/practice/mistakes", name: 'practiceMistakes', component: PracticeMistakes, meta: { allowedRoles: ['学生','VIP'] } },
    // 考纲/知识点练习
    { path: "/syllabus/setup", name: 'syllabusSetup', component: SyllabusSetup, meta: { allowedRoles: ['学生','VIP'] } },
    { path: "/syllabus/do", name: 'syllabusDo', component: SyllabusDo, meta: { allowedRoles: ['学生','VIP'] } },
    { path: "/syllabus/stats", name: 'syllabusStats', component: SyllabusStats, meta: { allowedRoles: ['学生','VIP'] } },
    // 新增：题目审查
    { path: "/review", name: 'review', component: Review, meta: { allowedRoles: ['学生','VIP'] } },
    { path: "/review/rank", name: 'reviewRank', component: ReviewRank, meta: { allowedRoles: ['学生','VIP','老师','管理员'] } },
    // 教师管理 - 审查统计
    { path: "/manage/review-stats", component: ReviewStatsManage, meta: { allowedRoles: ['老师','管理员'] } },
    { path: "/manage/review-detail/:id", component: ReviewDetailManage, meta: { allowedRoles: ['老师','管理员'] } },
    // 教师管理 - 考试
    {
        path: "/manage/exams",
        component: ExamManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/exams/new",
        component: ExamForm,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/exams/edit/:id",
        component: ExamForm,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    // 教师管理 - 题库
    {
        path: "/manage/questions",
        component: ManageQuestion,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/questions/new",
        component: QuestionForm,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/questions/edit/:id",
        component: QuestionForm,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/questions/advanced",
        component: QuestionAdvanced,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/scores",
        component: ScoreManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/students",
        component: StudentManage,
        meta: { allowedRoles: ['管理员'] }
    }
    ,
    {
        path: "/manage/signins",
        component: SigninsManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/face-supplements",
        component: FaceSupplementsManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/q-comments",
        component: QCommentsManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/syllabus",
        component: SyllabusManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/face-expiring",
        component: FaceExpiringManage,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    {
        path: "/manage/review-queue",
        component: ReviewQueue,
        meta: { allowedRoles: ['老师','管理员'] }
    }
    ,
    { path: "/contact", name: 'contact', component: Contact },
]

const router = createRouter({
    history: createWebHashHistory(),
    routes
})

// 路由访问白名单（无需登录）
const PUBLIC_ROUTES = new Set(['/', '/login', '/register', '/contact', '/signin', '/exam_select'])

function roleHome(role){
    if (role === '学生' || role === 'VIP') return '/student'
    if (role === '老师') return '/teacher'
    if (role === '管理员') return '/admin'
    return '/login'
}

router.beforeEach((to, from, next) => {
    try {
        if (PUBLIC_ROUTES.has(to.path)) return next()
        const uid = localStorage.getItem('user_id')
        if (!uid) return next({ path: '/login', query: { redirect: to.fullPath } })
        const role = localStorage.getItem('role') || ''
        const allowed = to.meta && Array.isArray(to.meta.allowedRoles) ? to.meta.allowedRoles : null
        if (allowed && role && !allowed.includes(role)) {
            // 角色不匹配，重定向到各自主页
            return next({ path: roleHome(role) })
        }
        if (allowed && !role) {
            // 无角色信息，要求重新登录以刷新角色
            return next({ path: '/login', query: { redirect: to.fullPath } })
        }
    } catch (e) { /* 忽略 */ }
    next()
})

export default router
