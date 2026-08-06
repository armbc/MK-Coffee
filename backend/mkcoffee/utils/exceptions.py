"""
统一异常处理，将所有 DRF 异常转为 { "code": xxx, "data": null, "msg": "..." } 格式。
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """自定义异常处理，统一响应格式"""
    response = drf_exception_handler(exc, context)

    if response is not None:
        # 取 DRF 给的错误详情
        detail = response.data
        http_status = response.status_code

        return Response(
            {
                "code": http_status,
                "data": None,
                "msg": _format_detail(detail),
            },
            status=http_status,
        )

    # 未捕获的异常 → 500
    return Response(
        {"code": 500, "data": None, "msg": "服务器内部错误"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _format_detail(detail):
    """格式化错误信息为字符串"""
    if isinstance(detail, dict):
        # 取第一个字段的第一个错误信息
        for key, value in detail.items():
            if isinstance(value, list):
                return f"{key}: {value[0]}"
            return str(value)
    if isinstance(detail, list):
        return str(detail[0]) if detail else ""
    return str(detail)
