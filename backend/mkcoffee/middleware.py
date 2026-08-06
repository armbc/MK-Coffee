"""
统一 API 响应格式中间件。
将所有成功响应包装为 { "code": 0, "data": ..., "msg": "ok" }
"""
import json
from django.http import JsonResponse


class ApiResponseMiddleware:
    """统一包装 JSON 响应"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 仅对 /api/ 路径生效
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        response = self.get_response(request)

        # 只包装成功的 JSON 响应（DRF 返回的）
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        if 200 <= response.status_code < 300:
            try:
                data = json.loads(response.content)
            except (json.JSONDecodeError, TypeError):
                return response

            # 跳过已包装的响应（已含 code/data/msg）
            if isinstance(data, dict) and "code" in data and "data" in data:
                return response

            wrapped = {
                "code": 0,
                "data": data,
                "msg": "ok",
            }
            return JsonResponse(wrapped, status=response.status_code)

        return response
