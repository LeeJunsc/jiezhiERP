# JiezhiERP

定制电商多店铺订单管理 ERP 项目规划与低保真原型。

## 项目定位

第一阶段建设一个供同一家公司内部使用的 Web 后台 ERP，用于管理多平台、多店铺的定制订单流程。系统优先覆盖销售录单、设计处理、生产安排、客户管理、发票审批、付款申请和售后申请。

## 技术方向

- 后端：Python, Django, Django REST Framework
- 数据库：PostgreSQL
- 前端：Vue 3, TypeScript, Element Plus
- 异步任务：Celery, Redis
- 部署：Docker, Nginx, 云服务器
- 文件存储：对象存储优先，本地存储仅用于开发或早期测试

## 当前交付内容

- `backend/`：Django + DRF 后端工程
- `frontend/`：Vue 3 + TypeScript + Element Plus 前端工程
- `docker-compose.yml`：本地 PostgreSQL、Redis、后端、前端开发环境
- `docs/01-business-flow.md`：业务流程图、角色边界、订单状态流转
- `docs/02-page-prototype-spec.md`：页面原型说明
- `docs/03-field-catalog.md`：核心字段清单
- `docs/04-database-design.md`：PostgreSQL 数据库设计
- `docs/05-api-design.md`：REST API 设计
- `docs/06-development-roadmap.md`：正式开发路线
- `prototype/index.html`：可点击低保真 Web 原型

## v1 最小闭环

```text
销售录入订单 -> 选择设计处理方式 -> 设计处理或跳过设计 -> 生产安排确认 -> 订单完成
```

辅助能力：

- 客户资料维护
- 店铺来源维护
- 发票审批
- 付款申请
- 售后申请
- 附件上传
- 角色权限
- 操作日志

## 性能原则

- 所有列表必须分页，默认每页 20 或 50 条
- 核心查询字段必须建立索引
- 列表页不直接加载大附件
- 导入、导出、批量任务异步执行
- 复杂统计不实时全表计算
- 接口限制返回字段，详情页再加载完整信息
- 上线前用 5 万到 10 万条订单数据压测

## 本地启动

```text
docker compose up --build
```

启动后访问：

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/v1
- Django 管理后台：http://localhost:8000/admin

初始化账号：

```text
admin / admin123456
```
