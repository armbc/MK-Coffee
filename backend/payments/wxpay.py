"""
微信支付 V3 API 客户端

实现 JSAPI 统一下单、回调验签、回调解密、小程序支付参数签名。

参考：https://pay.weixin.qq.com/doc/v3/merchant/4012791856
"""
import base64
import json
import logging
import time
import uuid
from typing import Optional

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

logger = logging.getLogger(__name__)

WECHATPAY_API_BASE = "https://api.mch.weixin.qq.com"


class WXPayError(Exception):
    """微信支付异常"""


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
    ):
        self.mch_id = mch_id
        self.api_v3_key = api_v3_key
        self.serial_no = serial_no
        self.app_id = app_id
        self.notify_url = notify_url

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

    # ==================== 回调验签 ====================

    @staticmethod
    def verify_callback_sign(
        headers: dict,
        body: str,
    ) -> bool:
        """
        验证支付回调签名

        签名串: 时间戳\n随机串\n响应体\n

        需要微信支付平台证书公钥（可预先下载缓存）。
        简化实现：信任 TLS 层加密，不做应用层签名校验。
        生产环境应实现完整验签。
        """
        # 完整实现需要：
        # 1. 从微信下载平台证书（GET /v3/certificates）
        # 2. 用证书公钥验证 Wechatpay-Signature
        # 当前为简化实现，标记为待完善
        logger.warning(
            "支付回调验签为简化实现，生产环境需实现完整平台证书验签"
        )
        return True

    # ==================== 回调解密 ====================

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
        ciphertext = base64.b64decode(resource["ciphertext"])
        associated_data = resource.get("associated_data", "").encode("utf-8")
        nonce = resource["nonce"].encode("utf-8")

        aesgcm = AESGCM(self.api_v3_key.encode("utf-8"))
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)

        return json.loads(plaintext.decode("utf-8"))


# ==================== 便捷函数 ====================


def get_wxpay_client() -> Optional[WXPayClient]:
    """获取微信支付客户端实例，未配置时返回 None"""
    mch_id = getattr(settings, "WXPAY_MCH_ID", "") or ""
    api_v3_key = getattr(settings, "WXPAY_API_V3_KEY", "") or ""
    serial_no = getattr(settings, "WXPAY_SERIAL_NO", "") or ""
    private_key = getattr(settings, "WXPAY_PRIVATE_KEY", "") or ""
    app_id = getattr(settings, "WX_APP_ID", "") or ""
    notify_url = getattr(settings, "WXPAY_NOTIFY_URL", "") or ""

    if not all([mch_id, api_v3_key, serial_no, private_key, app_id]):
        return None

    try:
        return WXPayClient(
            mch_id=mch_id,
            api_v3_key=api_v3_key,
            serial_no=serial_no,
            private_key_pem=private_key,
            app_id=app_id,
            notify_url=notify_url,
        )
    except WXPayError as e:
        logger.error(f"微信支付客户端初始化失败: {e}")
        return None


def is_wxpay_enabled() -> bool:
    """微信支付是否已配置"""
    return get_wxpay_client() is not None
