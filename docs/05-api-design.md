# REST API 设计

## 通用规范

- API 前缀：`/api/v1`
- 认证方式：Session 或 JWT，v1 推荐后台 Session，后续开放小程序时再扩展 JWT。
- 列表分页参数：`page`、`page_size`
- 默认分页：`page_size=20`
- 最大分页：`page_size=100`
- 时间字段使用 ISO 8601 格式。
- 金额字段使用字符串返回，避免前端浮点精度问题。

## 通用错误格式

```json
{
  "code": "VALIDATION_ERROR",
  "message": "提交的数据不完整",
  "fields": {
    "customer_id": "客户不能为空"
  }
}
```

## 订单接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/orders` | 订单列表 | 销售、设计、生产、财务、管理员 |
| POST | `/orders` | 新建订单草稿 | 销售、管理员 |
| GET | `/orders/{id}` | 订单详情 | 有订单可见权限的角色 |
| PATCH | `/orders/{id}` | 编辑订单 | 销售、管理员 |
| POST | `/orders/{id}/submit` | 提交订单，并按设计处理方式分流到设计任务或生产安排 | 销售、管理员 |
| POST | `/orders/{id}/cancel` | 取消订单 | 销售、管理员 |
| GET | `/orders/{id}/logs` | 操作日志 | 有订单可见权限的角色 |

订单列表筛选：

- `keyword`
- `store_id`
- `status`
- `salesperson_id`
- `created_from`
- `created_to`
- `delivery_from`
- `delivery_to`

## 设计任务接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/design-tasks` | 设计任务列表 | 设计、管理员 |
| GET | `/design-tasks/{id}` | 设计任务详情 | 设计、管理员 |
| POST | `/design-tasks/{id}/claim` | 领取任务 | 设计、管理员 |
| POST | `/design-tasks/{id}/upload-draft` | 上传设计稿 | 设计、管理员 |
| POST | `/design-tasks/{id}/request-changes` | 标记需修改 | 设计、管理员 |
| POST | `/design-tasks/{id}/confirm` | 设计确认并进入生产安排 | 设计、管理员 |

## 生产安排接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/production-arrangements` | 生产安排列表 | 生产、管理员 |
| GET | `/production-arrangements/{id}` | 生产安排详情 | 生产、管理员 |
| POST | `/production-arrangements/{id}/schedule` | 设置工厂代工安排 | 生产、管理员 |
| POST | `/production-arrangements/{id}/confirm` | 确认生产安排并完成订单 | 生产、管理员 |
| POST | `/production-arrangements/{id}/mark-exception` | 记录异常 | 生产、管理员 |

## 设计处理方式接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/design-options` | 设计处理方式列表 | 登录用户 |
| POST | `/design-options` | 新建设计处理方式 | 管理员 |
| PATCH | `/design-options/{id}` | 修改设计处理方式 | 管理员 |
| POST | `/design-options/{id}/disable` | 停用设计处理方式 | 管理员 |

## 客户接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/customers` | 客户列表 | 销售、财务、管理员 |
| POST | `/customers` | 新建客户 | 销售、管理员 |
| GET | `/customers/{id}` | 客户详情 | 销售、财务、管理员 |
| PATCH | `/customers/{id}` | 编辑客户 | 销售、管理员 |
| GET | `/customers/{id}/orders` | 客户订单 | 销售、财务、管理员 |

## 财务接口

发票申请：

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/invoice-requests` | 发票申请列表 | 财务、管理员 |
| POST | `/invoice-requests` | 新建发票申请 | 销售、财务、管理员 |
| GET | `/invoice-requests/{id}` | 发票申请详情 | 财务、管理员 |
| POST | `/invoice-requests/{id}/submit` | 提交审批 | 申请人、管理员 |
| POST | `/invoice-requests/{id}/approve` | 审批通过 | 财务、管理员 |
| POST | `/invoice-requests/{id}/reject` | 审批驳回 | 财务、管理员 |

付款申请：

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/payment-requests` | 付款申请列表 | 财务、管理员 |
| POST | `/payment-requests` | 新建付款申请 | 销售、财务、管理员 |
| GET | `/payment-requests/{id}` | 付款申请详情 | 财务、管理员 |
| POST | `/payment-requests/{id}/submit` | 提交审批 | 申请人、管理员 |
| POST | `/payment-requests/{id}/approve` | 审批通过 | 财务、管理员 |
| POST | `/payment-requests/{id}/reject` | 审批驳回 | 财务、管理员 |

## 售后接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/after-sales` | 售后列表 | 销售、售后、管理员 |
| POST | `/after-sales` | 新建售后申请 | 销售、售后、管理员 |
| GET | `/after-sales/{id}` | 售后详情 | 销售、售后、管理员 |
| POST | `/after-sales/{id}/accept` | 受理售后 | 售后、管理员 |
| POST | `/after-sales/{id}/resolve` | 完成售后 | 售后、管理员 |
| POST | `/after-sales/{id}/close` | 关闭售后 | 售后、管理员 |

## 附件接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/attachments` | 上传附件 | 登录用户 |
| GET | `/attachments` | 附件列表 | 业务可见用户 |
| DELETE | `/attachments/{id}` | 删除附件 | 上传人、管理员 |

## 系统接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/users` | 用户列表 | 管理员 |
| POST | `/users` | 创建用户 | 管理员 |
| PATCH | `/users/{id}` | 修改用户 | 管理员 |
| GET | `/roles` | 角色列表 | 管理员 |
| GET | `/stores` | 店铺列表 | 登录用户 |
| POST | `/stores` | 创建店铺 | 管理员 |

## 异步任务接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/imports/orders` | 上传订单导入文件 | 销售、管理员 |
| POST | `/exports/orders` | 创建订单导出任务 | 销售、管理员 |
| GET | `/tasks/{id}` | 查看异步任务状态 | 任务创建人、管理员 |
