---
name: mk-coffee
description: 苏州迈科咖啡微信小程序项目开发。当用户提到「迈科咖啡」「MK-Coffee」「咖啡小程序」或在此项目目录下工作时触发。
---

# 迈科咖啡微信小程序

## 项目上下文

- **路径**：`/home/mbc/Django/MK-Coffee/`
- **后端**：Django + Django REST Framework，路径 `backend/`
- **前端**：微信原生小程序（WXML + WXSS + JS），路径 `miniapp/`
- **数据库**：MySQL 8.0.44，通过个人云 ~/MySQL8/ 管理
- **完整计划**：`PLAN.md`

## 后端约定

- 虚拟环境使用项目自身的 `backend/.venv/`，不依赖系统 Python
- Django settings 分环境（`mkcoffee/settings/dev.py`、`production.py`）
- API 统一返回格式 `{ "code": 0, "data": {...}, "msg": "ok" }`
- 所有 API 使用 Django REST Framework 的 ViewSet + Router
- 微信登录使用 `jscode2session` 接口，JWT 鉴权
- CORS 配置通过 `django-cors-headers`
- 敏感配置（SECRET_KEY、数据库密码、微信 AppSecret）通过环境变量注入

## 小程序约定

- 使用微信原生框架，不做跨端
- API 请求封装在 `utils/api.js`，统一处理 token 和错误
- 页面路径遵循 `pages/<module>/<action>` 规范
- 图片等静态资源放在 `miniapp/images/`
- 基础库版本 ≥ 2.18.0

## 数据库与模型

- 表名使用下划线命名（`order_items`）
- 每张表包含 `created_at`、`updated_at` 时间戳
- 用户表以 `openid` 为唯一标识
- 订单使用 UUID 类型的 `order_no`

## 代码规范

- Python 遵循 PEP 8，使用 4 空格缩进
- JS 使用 2 空格缩进
- 所有 API 端点编写 DRF 测试
- Git 提交使用中文描述，格式：`[模块] 简要说明`

## 工作流程

1. 查看 `PLAN.md` 了解当前阶段
2. 每次改动聚焦一个模块
3. 修改后更新 `PLAN.md` 中的 checklist
4. 数据库变更同步更新 `PLAN.md` 中的表设计
