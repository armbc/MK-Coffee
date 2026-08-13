"""
微信支付 V3 API 客户端

实现 JSAPI 统一下单、回调验签、回调解密、小程序支付参数签名。

参考：https://pay.weixin.qq.com/doc/v3/merchant/4012791856
"""
import base64
import json
import logging
import os
import tempfile
import time
import uuid
from typing import Optional

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

logger = logging.getLogger(__name__)

WECHATPAY_API_BASE = "https://api.mch.weixin.qq.com"


class WXPayError(Exception):
    """微信支付异常"""


# 回调验签时间戳容忍窗口（防重放）
CALLBACK_TIMESTAMP_TOLERANCE = 300


def _header(headers, name: str) -> str:
    """大小写不敏感地读取请求头（兼容 dict 与 Django HttpHeaders）"""
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


class WXPayClient:
    """微信支付 V3 客户端"""

    def __init__(
        self,
        mch_id: str,
        api_v3_key: str,
        serial_no: str,
        private_key_pem: str,
        app_id: str,
        notify_url: str,
        cert_path: str = "",
    ):
        self.mch_id = mch_id
        self.api_v3_key = api_v3_key
        self.serial_no = serial_no
        self.app_id = app_id
        self.notify_url = notify_url
        self.cert_path = cert_path
        self._certs = None  # 实例级平台证书缓存 {serial_no: pem}

        # APIv3 密钥必须是 32 字节，提前校验避免运行时才暴露
        if len(api_v3_key.encode("utf-8")) != 32:
            raise WXPayError("WXPAY_API_V3_KEY 必须为 32 字节")

        # 加载商户私钥
        try:
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
            )
        except Exception as e:
            raise WXPayError(f"加载商户私钥失败: {e}")

    # ==================== 签名工具 ====================

    def _sign(self, sign_str: str) -> str:
        """SHA256-RSA2048 签名"""
        signature = self._private_key.sign(
            sign_str.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def _make_authorization(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> str:
        """生成请求 Authorization 头"""
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex[:32]

        # 签名串: HTTP方法\nURL路径\n时间戳\n随机串\n请求体\n
        sign_str = f"{method}\n{path}\n{timestamp}\n{nonce_str}\n{body}\n"
        signature = self._sign(sign_str)

        return (
            f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",'
            f'nonce_str="{nonce_str}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.serial_no}",'
            f'signature="{signature}"'
        )

    # ==================== 请求封装 ====================

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """发送带签名的请求"""
        url = f"{WECHATPAY_API_BASE}{path}"
        body_str = json.dumps(body) if body else ""

        headers = {
            "Authorization": self._make_authorization(method, path, body_str),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=body_str if body_str else None,
            timeout=15,
        )

        if resp.status_code >= 400:
            raise WXPayError(
                f"微信支付请求失败 [{resp.status_code}]: {resp.text}"
            )

        return resp.json()

    # ==================== JSAPI 统一下单 ====================

    def jsapi_order(
        self,
        out_trade_no: str,
        amount: int,  # 单位：分
        payer_openid: str,
        description: str,
    ) -> dict:
        """
        JSAPI 统一下单

        返回微信支付响应，包含 prepay_id。

        Args:
            out_trade_no: 商户订单号
            amount: 支付金额（分）
            payer_openid: 用户 openid
            description: 商品描述

        Returns:
            {"prepay_id": "wx..."}
        """
        body = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description[:127],  # 最长 127 字符
            "out_trade_no": out_trade_no,
            "notify_url": self.notify_url,
            "amount": {
                "total": amount,
                "currency": "CNY",
            },
            "payer": {
                "openid": payer_openid,
            },
        }

        return self._request("POST", "/v3/pay/transactions/jsapi", body)

    # ==================== 小程序支付参数签名 ====================

    def sign_miniapp_params(self, prepay_id: str) -> dict:
        """
        生成小程序调起支付所需的参数

        签名串: appId\n时间戳\n随机串\nprepay_id=xxx\n
        """
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex[:32]
        package = f"prepay_id={prepay_id}"

        sign_str = f"{self.app_id}\n{timestamp}\n{nonce_str}\n{package}\n"

        return {
            "appId": self.app_id,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "RSA",
            "paySign": self._sign(sign_str),
        }

    # ==================== 平台证书管理 ====================

    def _load_cached_certificates(self) -> dict:
        """读取缓存的微信支付平台证书 {serial_no: pem}"""
        if self._certs is not None:
            return self._certs
        certs = {}
        if self.cert_path and os.path.exists(self.cert_path):
            try:
                with open(self.cert_path, "r", encoding="utf-8") as f:
                    certs = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("平台证书缓存读取失败，将重新下载: %s", e)
                certs = {}
        self._certs = certs
        return certs

    def _save_certificates(self, certs: dict) -> None:
        """写入平台证书缓存（权限 600）"""
        if not self.cert_path:
            return
        try:
            with open(self.cert_path, "w", encoding="utf-8") as f:
                json.dump(certs, f)
            os.chmod(self.cert_path, 0o600)
        except OSError as e:
            logger.warning("平台证书缓存写入失败: %s", e)

    def _download_platform_certificates(self) -> dict:
        """
        下载并解密微信支付平台证书（GET /v3/certificates）

        返回 {serial_no: pem}，合并进本地缓存。
        """
        try:
            result = self._request("GET", "/v3/certificates")
        except Exception as e:
            raise WXPayError(f"下载微信平台证书失败: {e}")

        certs = {}
        for item in result.get("data", []):
            serial = item.get("serial_no")
            enc = item.get("encrypt_certificate")
            if not serial or not enc:
                continue
            try:
                certs[serial] = self._aesgcm_decrypt(enc)
            except Exception as e:
                logger.warning("解密平台证书 %s 失败: %s", serial, e)

        if not certs:
            raise WXPayError("微信平台证书列表为空")

        merged = {**self._load_cached_certificates(), **certs}
        self._certs = merged
        self._save_certificates(merged)
        logger.info("已更新 %d 个微信支付平台证书", len(certs))
        return merged

    def _get_platform_certificates(self, serial: str = "") -> dict:
        """获取平台证书；本地缺少指定序列号时刷新一次（证书轮换场景）"""
        certs = self._load_cached_certificates()
        if serial and serial not in certs:
            try:
                certs = self._download_platform_certificates()
            except WXPayError as e:
                logger.error("刷新平台证书失败: %s", e)
        return certs

    # ==================== 回调验签 ====================

    def verify_callback_sign(self, headers, body: str) -> bool:
        """
        验证支付回调签名（微信支付平台证书，RSA-SHA256）

        签名串: 时间戳\n随机串\n请求体\n
        请求头:
            Wechatpay-Timestamp / Wechatpay-Nonce /
            Wechatpay-Signature / Wechatpay-Serial
        """
        timestamp = _header(headers, "Wechatpay-Timestamp")
        nonce = _header(headers, "Wechatpay-Nonce")
        signature = _header(headers, "Wechatpay-Signature")
        serial = _header(headers, "Wechatpay-Serial")

        if not all([timestamp, nonce, signature, serial]):
            logger.warning("回调缺少验签请求头")
            return False

        # 防重放：时间戳偏差超过容忍窗口直接拒绝
        try:
            if abs(int(time.time()) - int(timestamp)) > CALLBACK_TIMESTAMP_TOLERANCE:
                logger.warning("回调时间戳超出容忍窗口")
                return False
        except (TypeError, ValueError):
            return False

        sign_str = f"{timestamp}\n{nonce}\n{body}\n"

        certs = self._get_platform_certificates(serial)
        pem = certs.get(serial)
        if not pem:
            logger.warning("未找到序列号为 %s 的平台证书", serial)
            return False

        try:
            cert = x509.load_pem_x509_certificate(pem.encode("utf-8"))
            cert.public_key().verify(
                base64.b64decode(signature),
                sign_str.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            logger.warning("回调签名校验失败")
            return False
        except Exception as e:
            logger.error("回调验签异常: %s", e)
            return False

    # ==================== 回调解密 ====================

    def _aesgcm_decrypt(self, resource: dict) -> str:
        """AEAD_AES_256_GCM 解密，返回明文字符串"""
        ciphertext = base64.b64decode(resource["ciphertext"])
        associated_data = resource.get("associated_data", "").encode("utf-8")
        nonce = resource["nonce"].encode("utf-8")

        aesgcm = AESGCM(self.api_v3_key.encode("utf-8"))
        return aesgcm.decrypt(nonce, ciphertext, associated_data).decode("utf-8")

    def decrypt_callback(self, resource: dict) -> dict:
        """
        解密回调通知中的加密数据

        Args:
            resource: 回调中的 resource 字段
                {
                    "ciphertext": "...",
                    "associated_data": "...",
                    "nonce": "..."
                }

        Returns:
            解密后的 JSON 数据
        """
        return json.loads(self._aesgcm_decrypt(resource))


# ==================== 便捷函数 ====================


def get_wxpay_client() -> Optional[WXPayClient]:
    """
    获取微信支付客户端实例。

    - ``WXPAY_ENABLED=false``（默认）→ 返回 ``None``，调用方走模拟支付
    - ``WXPAY_ENABLED=true`` 但配置缺失或初始化失败 → 抛 ``WXPayError``

    设计原则：fail-closed。已显式启用微信支付却不可用时，绝不允许
    静默降级为模拟支付（否则任何配置失误都会导致“免费下单”）。
    """
    if not getattr(settings, "WXPAY_ENABLED", False):
        return None

    conf = {
        "WXPAY_MCH_ID": getattr(settings, "WXPAY_MCH_ID", "") or "",
        "WXPAY_API_V3_KEY": getattr(settings, "WXPAY_API_V3_KEY", "") or "",
        "WXPAY_SERIAL_NO": getattr(settings, "WXPAY_SERIAL_NO", "") or "",
        "WXPAY_PRIVATE_KEY": getattr(settings, "WXPAY_PRIVATE_KEY", "") or "",
        "WX_APP_ID": getattr(settings, "WX_APP_ID", "") or "",
        "WXPAY_NOTIFY_URL": getattr(settings, "WXPAY_NOTIFY_URL", "") or "",
    }
    missing = [name for name, value in conf.items() if not value]
    if missing:
        raise WXPayError(
            f"WXPAY_ENABLED=true 但配置缺失: {', '.join(missing)}"
        )

    cert_path = getattr(settings, "WXPAY_CERT_PATH", "") or ""
    if not cert_path:
        cert_path = os.path.join(
            tempfile.gettempdir(), "mkcoffee_wxpay_certs.json"
        )

    try:
        return WXPayClient(
            mch_id=conf["WXPAY_MCH_ID"],
            api_v3_key=conf["WXPAY_API_V3_KEY"],
            serial_no=conf["WXPAY_SERIAL_NO"],
            private_key_pem=conf["WXPAY_PRIVATE_KEY"],
            app_id=conf["WX_APP_ID"],
            notify_url=conf["WXPAY_NOTIFY_URL"],
            cert_path=cert_path,
        )
    except WXPayError:
        raise
    except Exception as e:
        raise WXPayError(f"微信支付客户端初始化失败: {e}")


def is_wxpay_enabled() -> bool:
    """微信支付是否已启用且可用"""
    try:
        return get_wxpay_client() is not None
    except WXPayError:
        return False
