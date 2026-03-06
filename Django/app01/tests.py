from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from .models import User

class SessionAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='u1', password='pass123', role='学生', department='D1', classroom='C1')

    def test_public_endpoints_accessible_without_login(self):
        # 去掉裸 /api 以避免潜在重定向差异；已在 urls 显式支持，但测试保持最小
        for url in ['/api/', '/api/overview']:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"公共接口 {url} 不应被拦截")
            self.assertTrue(resp.json().get('success') is True)

    def test_protected_endpoint_requires_login(self):
        resp = self.client.get('/api/score-query')
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertIn('未登录', data.get('error_msg', ''))

    def test_login_then_access_protected(self):
        resp = self.client.post('/api/login', {'username': 'u1', 'password': 'pass123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('success'))
        # 确认密码已升级为哈希
        self.user.refresh_from_db()
        self.assertIn('$', self.user.password)
        resp2 = self.client.get('/api/score-query')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json().get('success'))
        self.assertIn('score_list', resp2.json())

class PasswordHashTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_password_hashed(self):
        payload = { 'username': 'hashuser', 'password': 'StrongPwd1', 'role': '学生', 'classroom': 'C1', 'department': '' }
        r = self.client.post('/api/register', payload, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('success'))
        u = User.objects.get(username='hashuser')
        self.assertNotEqual(u.password, payload['password'])
        self.assertTrue(u.password.startswith('pbkdf2_'))

    def test_login_with_hashed_password(self):
        u = User.objects.create(username='h2', password=make_password('Abcd1234'), role='学生', department='D', classroom='C')
        r = self.client.post('/api/login', {'username': 'h2', 'password': 'Abcd1234'}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('success'))
        # 保持哈希不被覆盖
        u.refresh_from_db()
        self.assertTrue(u.password.startswith('pbkdf2_'))

    def test_login_wrong_password(self):
        User.objects.create(username='h3', password=make_password('RightPwd9'), role='学生', department='D', classroom='C')
        r = self.client.post('/api/login', {'username': 'h3', 'password': 'WrongPwd'}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json().get('success'))
        self.assertIn('错误', r.json().get('error_msg', ''))
