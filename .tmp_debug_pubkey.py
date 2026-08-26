"""调试：尝试多个微信支付公钥接口路径"""
from payments.wxpay import get_wxpay_client, WECHATPAY_API_BASE
import requests
import time

c = get_wxpay_client()
paths = [
    "/v3/certificates/public-key",
    "/v3/certificates/public-key?algorithm_type=RSA",
    "/v3/certificates?algorithm_type=RSA",
    "/v3/certificates",
]
for path in paths:
    ts = str(int(time.time()))
    nonce = "dbg" + path[-6:].replace("/", "x")
    sign_str = f"GET\n{path}\n{ts}\n{nonce}\n\n"
    sig = c._sign(sign_str)
    auth = (
        'WECHATPAY2-SHA256-RSA2048 mchid="' + c.mch_id
        + '",nonce_str="' + nonce
        + '",signature="' + sig
        + '",timestamp="' + ts
        + '",serial_no="' + c.serial_no + '"'
    )
    r = requests.get(
        WECHATPAY_API_BASE + path,
        headers={"Authorization": auth, "Accept": "application/json"},
        timeout=15,
    )
    print(f"路径: {path}")
    print(f"  状态码: {r.status_code}")
    print(f"  响应体: {r.text[:200]!r}")
