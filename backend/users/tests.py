"""用户模块 · 测试"""
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserModelTest(TestCase):
    """用户模型测试"""

    def test_create_user(self):
        user = User.objects.create(
            openid="test_openid_123",
            nickname="测试用户",
            avatar="https://example.com/avatar.png",
            phone="13800138000",
        )
        self.assertEqual(user.openid, "test_openid_123")
        self.assertEqual(user.nickname, "测试用户")
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)

    def test_openid_unique(self):
        User.objects.create(openid="dup_openid")
        with self.assertRaises(Exception):
            User.objects.create(openid="dup_openid")

    def test_openid_uniqueness(self):
        User.objects.create(openid="dup_openid", nickname="first")
        with self.assertRaises(Exception):
            User.objects.create(openid="dup_openid", nickname="second")


class WxLoginAPITest(TestCase):
    """微信登录 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("auth-wx-login")

    def test_missing_code(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 400)

    @patch("users.views.requests.get")
    def test_wx_login_success_new_user(self, mock_get):
        mock_get.return_value.json.return_value = {
            "openid": "wx_openid_new",
            "session_key": "sk_test",
        }
        mock_get.return_value.status_code = 200

        resp = self.client.post(self.url, {"code": "valid_code"}, format="json")
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["is_new"])
        self.assertIn("access", data["data"])
        self.assertIn("refresh", data["data"])
        self.assertEqual(data["data"]["user"]["nickname"], "")

    @patch("users.views.requests.get")
    def test_wx_login_existing_user(self, mock_get):
        User.objects.create(openid="wx_openid_existing", nickname="老用户")
        mock_get.return_value.json.return_value = {
            "openid": "wx_openid_existing",
            "session_key": "sk_test",
        }
        mock_get.return_value.status_code = 200

        resp = self.client.post(self.url, {
            "code": "valid_code",
            "nickname": "新昵称",
        }, format="json")
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertFalse(data["data"]["is_new"])
        self.assertEqual(data["data"]["user"]["nickname"], "新昵称")

    @patch("users.views.requests.get")
    def test_wx_login_api_failure(self, mock_get):
        mock_get.return_value.json.return_value = {
            "errcode": 40029,
            "errmsg": "invalid code",
        }
        mock_get.return_value.status_code = 200

        resp = self.client.post(self.url, {"code": "bad_code"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("微信登录失败", resp.json()["msg"])


class UserProfileAPITest(TestCase):
    """用户信息接口测试"""

    def setUp(self):
        self.user = User.objects.create(
            openid="profile_user_openid",
            nickname="个人信息用户",
            phone="13900139000",
        )
        self.client = APIClient()
        # 获取 token 并设置认证头
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.url = reverse("user-detail", kwargs={"pk": self.user.pk})

    def test_get_profile(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["nickname"], "个人信息用户")
        self.assertEqual(data["data"]["phone"], "13900139000")

    def test_get_profile_me(self):
        """GET /api/user/me/ 当前用户（小程序实际调用路径）"""
        resp = self.client.get(reverse("user-me"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["nickname"], "个人信息用户")

    def test_update_profile(self):
        resp = self.client.put(self.url, {"nickname": "新昵称"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "新昵称")

    def test_update_nickname_post(self):
        """POST 版本昵称更新（小程序用）"""
        resp = self.client.post(
            reverse("user-update-profile"),
            {"nickname": "POST昵称"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "POST昵称")

    def test_update_nickname_empty(self):
        resp = self.client.post(
            reverse("user-update-profile"),
            {"nickname": "  "},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_upload_avatar(self):
        """头像上传：multipart 文件 → 返回 URL"""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), "orange").save(buf, "PNG")
        file = SimpleUploadedFile(
            "avatar.png", buf.getvalue(), content_type="image/png",
        )
        resp = self.client.post(
            reverse("user-upload-avatar"),
            {"avatar": file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["avatar"].startswith("http://testserver/media/avatars/"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar.endswith(".png"))

    def test_unauthenticated(self):
        client = APIClient()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 401)


class AddressTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(openid="addr_user")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_address(self):
        resp = self.client.post("/api/addresses/", {
            "name": "张三", "phone": "13800138000",
            "province": "江苏省", "city": "苏州市",
            "district": "工业园区", "detail": "某某路100号",
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["data"]["name"], "张三")

    def test_first_address_is_default(self):
        resp = self.client.post("/api/addresses/", {
            "name": "张三", "phone": "13800138000",
            "province": "江苏省", "city": "苏州市",
            "district": "工业园区", "detail": "某某路100号",
        })
        self.assertTrue(resp.json()["data"]["is_default"])

    def test_set_default(self):
        self.client.post("/api/addresses/", {
            "name": "张三", "phone": "13800138000",
            "province": "江苏省", "city": "苏州市",
            "district": "工业园区", "detail": "地址A",
        })
        resp = self.client.post("/api/addresses/", {
            "name": "李四", "phone": "13900139000",
            "province": "江苏省", "city": "苏州市",
            "district": "工业园区", "detail": "地址B",
        })
        addr2_id = resp.json()["data"]["id"]
        self.client.post(f"/api/addresses/{addr2_id}/set-default/")
        # 验证只有地址B是默认
        list_resp = self.client.get("/api/addresses/")
        addrs = list_resp.json()["data"]["results"]
        self.assertEqual(len([a for a in addrs if a["is_default"]]), 1)
        self.assertEqual(addrs[0]["name"], "李四")

    def test_delete_address(self):
        resp = self.client.post("/api/addresses/", {
            "name": "张三", "phone": "13800138000",
            "province": "江苏省", "city": "苏州市",
            "district": "工业园区", "detail": "地址",
        })
        addr_id = resp.json()["data"]["id"]
        resp = self.client.delete(f"/api/addresses/{addr_id}/")
        self.assertEqual(resp.status_code, 204)

    def test_unauthorized(self):
        unauth = APIClient()
        resp = unauth.get("/api/addresses/")
        self.assertEqual(resp.status_code, 401)
