"""支付模块 · 测试

覆盖：
- get_wxpay_client 的 fail-closed 行为（防止静默降级为模拟支付）
- 微信支付回调验签（平台证书 RSA-SHA256 + 防重放时间戳）
- 支付入口：模拟支付 / 启用微信支付但配置错误时拒绝支付
- 支付回调端到端：验签 → 解密 → 商户/金额校验 → 更新订单
"""
import base64
import datetime
import json
import os
import tempfile
import time
from decimal import Decimal

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.x509.oid import NameOID
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import User

from .models import PaymentRecord
from .wxpay import WXPayClient, WXPayError, get_wxpay_client


# ==================== 测试辅助 ====================


def _make_key_pair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _private_pem(private_key) -> str:
    return private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")


def _self_signed_cert_pem(private_key) -> str:
    """生成自签名"平台证书"（仅用于测试验签逻辑）"""
    now = datetime.datetime.now(datetime.timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "WXPay Test CA")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")


def _write_cert_cache(certs: dict) -> str:
    """写入平台证书缓存文件，返回路径"""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(certs, f)
    return path


# ==================== get_wxpay_client 行为 ====================


class GetWXPayClientTest(TestCase):
    """fail-closed：启用微信支付但配置不可用时必须抛错，不得静默降级"""

    @override_settings(WXPAY_ENABLED=False)
    def test_disabled_returns_none(self):
        self.assertIsNone(get_wxpay_client())

    @override_settings(
        WXPAY_ENABLED=True,
        WXPAY_MCH_ID="",
        WXPAY_API_V3_KEY="",
        WXPAY_SERIAL_NO="",
        WXPAY_PRIVATE_KEY="",
        WXPAY_NOTIFY_URL="",
    )
    def test_enabled_but_missing_config_raises(self):
        with self.assertRaises(WXPayError):
            get_wxpay_client()

    def test_enabled_with_full_config_returns_client(self):
        with override_settings(
            WXPAY_ENABLED=True,
            WXPAY_MCH_ID="mch_test",
            WXPAY_API_V3_KEY="k" * 32,
            WXPAY_SERIAL_NO="serial_test",
            WXPAY_PRIVATE_KEY=_private_pem(_make_key_pair()),
            WX_APP_ID="wx_test",
            WXPAY_NOTIFY_URL="https://example.com/callback/",
            WXPAY_CERT_PATH="",
        ):
            client = get_wxpay_client()
            self.assertIsInstance(client, WXPayClient)

    def test_bad_api_v3_key_length_rejected(self):
        """APIv3 密钥必须为 32 字节"""
        mch_pem = _private_pem(_make_key_pair())
        with self.assertRaises(WXPayError):
            WXPayClient(
                mch_id="m",
                api_v3_key="too-short",
                serial_no="s",
                private_key_pem=mch_pem,
                app_id="a",
                notify_url="https://example.com/cb/",
            )


# ==================== 回调验签 ====================


class CallbackSignVerifyTest(TestCase):
    def setUp(self):
        self.platform_key = _make_key_pair()
        mch_pem = _private_pem(_make_key_pair())
        self.platform_serial = "PLATFORM_SERIAL_TEST"
        self.cert_path = _write_cert_cache({
            self.platform_serial: _self_signed_cert_pem(self.platform_key),
        })
        self.client = WXPayClient(
            mch_id="mch_test",
            api_v3_key="k" * 32,
            serial_no="mch_serial",
            private_key_pem=mch_pem,
            app_id="wx_test",
            notify_url="https://example.com/cb/",
            cert_path=self.cert_path,
        )

    def tearDown(self):
        os.unlink(self.cert_path)

    def _signed_headers(self, body: str, timestamp=None, sign_key=None) -> dict:
        ts = str(timestamp if timestamp is not None else int(time.time()))
        nonce = "testnonce123"
        key = sign_key or self.platform_key
        sign_str = f"{ts}\n{nonce}\n{body}\n"
        signature = base64.b64encode(
            key.sign(sign_str.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
        ).decode("utf-8")
        return {
            "Wechatpay-Timestamp": ts,
            "Wechatpay-Nonce": nonce,
            "Wechatpay-Signature": signature,
            "Wechatpay-Serial": self.platform_serial,
        }

    def test_valid_signature_passes(self):
        body = '{"id":"evt-1"}'
        self.assertTrue(
            self.client.verify_callback_sign(self._signed_headers(body), body)
        )

    def test_tampered_body_fails(self):
        headers = self._signed_headers('{"id":"evt-1"}')
        self.assertFalse(
            self.client.verify_callback_sign(headers, '{"id":"evt-2"}')
        )

    def test_wrong_key_fails(self):
        body = '{"id":"evt-1"}'
        headers = self._signed_headers(body, sign_key=_make_key_pair())
        self.assertFalse(self.client.verify_callback_sign(headers, body))

    def test_expired_timestamp_fails(self):
        body = '{"id":"evt-1"}'
        headers = self._signed_headers(body, timestamp=int(time.time()) - 400)
        self.assertFalse(self.client.verify_callback_sign(headers, body))

    def test_missing_headers_fail(self):
        self.assertFalse(self.client.verify_callback_sign({}, "body"))

    def test_unknown_serial_fails(self):
        """未知证书序列号且无法下载新证书 → 拒绝"""
        body = '{"id":"evt-1"}'
        headers = self._signed_headers(body)
        headers["Wechatpay-Serial"] = "UNKNOWN_SERIAL"
        self.assertFalse(self.client.verify_callback_sign(headers, body))


# ==================== 支付入口 ====================


class PayAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create(openid="pay_test_user")
        self.cat = Category.objects.create(name="支付测试分类")
        self.product = Product.objects.create(
            name="支付测试商品", category=self.cat,
            price=Decimal("50.00"), stock=10,
        )
        self.order = Order.objects.create(user=self.user, total=Decimal("50.00"))
        OrderItem.objects.create(
            order=self.order, product=self.product,
            product_name=self.product.name, price=self.product.price, quantity=1,
        )
        self.api = APIClient()
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}"
        )
        self.url = f"/api/orders/{self.order.id}/pay/"

    @override_settings(WXPAY_ENABLED=False)
    def test_mock_pay_when_disabled(self):
        """未启用微信支付 → 模拟支付（现有行为保持）"""
        resp = self.api.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        record = PaymentRecord.objects.get(order=self.order)
        self.assertEqual(record.method, "mock")
        self.assertEqual(record.status, "paid")

    @override_settings(
        WXPAY_ENABLED=True,
        WXPAY_MCH_ID="",
        WXPAY_API_V3_KEY="",
        WXPAY_SERIAL_NO="",
        WXPAY_PRIVATE_KEY="",
        WXPAY_NOTIFY_URL="",
    )
    def test_fail_closed_when_enabled_but_broken(self):
        """已启用微信支付但配置缺失 → 拒绝支付，订单保持待支付"""
        resp = self.api.post(self.url)
        self.assertEqual(resp.status_code, 500)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertFalse(PaymentRecord.objects.filter(order=self.order).exists())


# ==================== 支付回调端到端 ====================


class PaymentCallbackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(openid="cb_test_user")
        self.cat = Category.objects.create(name="回调分类")
        self.product = Product.objects.create(
            name="回调商品", category=self.cat, price=Decimal("88.00"), stock=10,
        )
        self.order = Order.objects.create(user=self.user, total=Decimal("88.00"))
        OrderItem.objects.create(
            order=self.order, product=self.product,
            product_name=self.product.name, price=self.product.price, quantity=1,
        )
        PaymentRecord.objects.create(
            order=self.order, user=self.user,
            method="wechat_jsapi", amount=self.order.total,
            prepay_id="prepay_test",
        )

        self.mch_key = _make_key_pair()
        self.platform_key = _make_key_pair()
        self.platform_serial = "PLATFORM_SERIAL_CB"
        self.api_v3_key = "c" * 32
        self.cert_path = _write_cert_cache({
            self.platform_serial: _self_signed_cert_pem(self.platform_key),
        })

        self._override = override_settings(
            WXPAY_ENABLED=True,
            WXPAY_MCH_ID="mch_cb",
            WXPAY_API_V3_KEY=self.api_v3_key,
            WXPAY_SERIAL_NO="mch_serial",
            WXPAY_PRIVATE_KEY=_private_pem(self.mch_key),
            WX_APP_ID="wx_cb",
            WXPAY_NOTIFY_URL="https://example.com/api/payments/callback/",
            WXPAY_CERT_PATH=self.cert_path,
        )
        self._override.enable()
        self.url = "/api/payments/callback/"

    def tearDown(self):
        self._override.disable()
        os.unlink(self.cert_path)

    def _build_callback(self, payload: dict, sign_key=None) -> tuple:
        """构造加密的回调请求体与验签头（模拟微信侧行为）"""
        enc_nonce = "0123456789ab"
        ciphertext = AESGCM(self.api_v3_key.encode("utf-8")).encrypt(
            enc_nonce.encode("utf-8"),
            json.dumps(payload).encode("utf-8"),
            b"transaction",
        )
        body = json.dumps({
            "id": "evt-test",
            "create_time": "2026-08-13T00:00:00+08:00",
            "resource_type": "encrypt-resource",
            "event_type": "TRANSACTION.SUCCESS",
            "resource": {
                "algorithm": "AEAD_AES_256_GCM",
                "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
                "associated_data": "transaction",
                "nonce": enc_nonce,
            },
        })
        ts = str(int(time.time()))
        header_nonce = "headernonce456"
        sign_str = f"{ts}\n{header_nonce}\n{body}\n"
        key = sign_key or self.platform_key
        signature = base64.b64encode(
            key.sign(sign_str.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
        ).decode("utf-8")
        headers = {
            "HTTP_WECHATPAY_TIMESTAMP": ts,
            "HTTP_WECHATPAY_NONCE": header_nonce,
            "HTTP_WECHATPAY_SIGNATURE": signature,
            "HTTP_WECHATPAY_SERIAL": self.platform_serial,
        }
        return body, headers

    def _valid_payload(self) -> dict:
        return {
            "appid": "wx_cb",
            "mchid": "mch_cb",
            "out_trade_no": self.order.order_no,
            "transaction_id": "wx_txn_123",
            "trade_state": "SUCCESS",
            "amount": {"total": 8800, "currency": "CNY"},
        }

    def test_callback_success_marks_order_paid(self):
        body, headers = self._build_callback(self._valid_payload())
        resp = APIClient().post(
            self.url, data=body, content_type="application/json", **headers,
        )
        self.assertEqual(resp.status_code, 200)
        # 中间件不得包装回调响应（微信协议）
        self.assertEqual(resp.json(), {"code": "SUCCESS"})

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        record = PaymentRecord.objects.get(order=self.order)
        self.assertEqual(record.status, "paid")
        self.assertEqual(record.transaction_id, "wx_txn_123")

    def test_callback_amount_mismatch_rejected(self):
        payload = self._valid_payload()
        payload["amount"]["total"] = 1  # 金额不符
        body, headers = self._build_callback(payload)
        resp = APIClient().post(
            self.url, data=body, content_type="application/json", **headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_callback_wrong_mchid_rejected(self):
        payload = self._valid_payload()
        payload["mchid"] = "other_mch"
        body, headers = self._build_callback(payload)
        resp = APIClient().post(
            self.url, data=body, content_type="application/json", **headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_callback_bad_signature_rejected(self):
        body, headers = self._build_callback(
            self._valid_payload(), sign_key=_make_key_pair(),
        )
        resp = APIClient().post(
            self.url, data=body, content_type="application/json", **headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_callback_forged_plaintext_rejected(self):
        """攻击者无 api_v3_key/平台私钥，伪造请求必然失败"""
        body = json.dumps({
            "id": "evt-fake",
            "event_type": "TRANSACTION.SUCCESS",
            "resource": {
                "ciphertext": base64.b64encode(b"fake").decode(),
                "associated_data": "transaction",
                "nonce": "0123456789ab",
            },
        })
        resp = APIClient().post(self.url, data=body, content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    @override_settings(WXPAY_ENABLED=False)
    def test_callback_when_disabled(self):
        """未启用微信支付时收到回调 → 明确拒绝"""
        resp = APIClient().post(
            self.url, data="{}", content_type="application/json",
        )
        self.assertEqual(resp.status_code, 500)
