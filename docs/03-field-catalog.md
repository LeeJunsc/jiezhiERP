# 字段清单

## 店铺 Store

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 店铺名称 |
| platform | enum | 是 | 平台，如淘宝、拼多多、抖音、小红书、其他 |
| owner_id | user_id | 否 | 店铺负责人 |
| status | enum | 是 | 启用、停用 |

## 设计处理方式 DesignOption

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 选项名称，如新订单需要设计、老订单修改、仅标注、续订无需设计 |
| requires_design | boolean | 是 | 是否需要生成设计任务 |
| sort_order | integer | 是 | 前端显示排序 |
| status | enum | 是 | 启用、停用 |
| description | text | 否 | 说明 |

## 客户 Customer

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 客户姓名或客户名称 |
| phone | string | 否 | 手机号 |
| wechat | string | 否 | 微信号 |
| address | text | 否 | 收货地址 |
| invoice_title | string | 否 | 发票抬头 |
| tax_number | string | 否 | 税号 |
| remark | text | 否 | 备注 |

## 订单 Order

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| order_no | string | 是 | 系统订单号，自动生成 |
| platform_order_no | string | 否 | 平台订单号，手工录入 |
| store_id | foreign_key | 是 | 所属店铺 |
| customer_id | foreign_key | 是 | 客户 |
| salesperson_id | user_id | 是 | 销售负责人 |
| design_option_id | foreign_key | 是 | 设计处理方式 |
| status | enum | 是 | 订单状态 |
| total_amount | decimal | 是 | 订单总金额 |
| paid_amount | decimal | 否 | 已收金额 |
| payment_status | enum | 是 | 未收款、部分收款、已收款 |
| delivery_date | date | 否 | 期望交付日期 |
| urgent | boolean | 是 | 是否加急 |
| customization_note | text | 否 | 定制说明 |
| remark | text | 否 | 内部备注 |
| submitted_at | datetime | 否 | 提交时间 |
| completed_at | datetime | 否 | 完成时间 |

## 订单明细 OrderItem

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| order_id | foreign_key | 是 | 关联订单 |
| product_name | string | 是 | 商品名称 |
| sku | string | 否 | 规格型号 |
| quantity | integer | 是 | 数量 |
| unit_price | decimal | 是 | 单价 |
| line_amount | decimal | 是 | 小计 |
| custom_size | string | 否 | 定制尺寸 |
| custom_color | string | 否 | 定制颜色 |
| custom_note | text | 否 | 单品定制要求 |

## 设计任务 DesignTask

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| task_no | string | 是 | 设计任务号 |
| order_id | foreign_key | 是 | 关联订单 |
| designer_id | user_id | 否 | 设计负责人 |
| status | enum | 是 | 待领取、设计中、待确认、需修改、已确认 |
| due_at | datetime | 否 | 截止时间 |
| confirmed_at | datetime | 否 | 确认时间 |
| remark | text | 否 | 设计备注 |

## 生产安排 ProductionArrangement

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| arrangement_no | string | 是 | 生产安排号 |
| order_id | foreign_key | 是 | 关联订单 |
| owner_id | user_id | 否 | 生产负责人 |
| factory_name | string | 否 | 代工工厂 |
| status | enum | 是 | 待安排、已安排、已确认、异常 |
| planned_finish_at | datetime | 否 | 计划交付时间 |
| confirmed_at | datetime | 否 | 安排确认时间 |
| remark | text | 否 | 生产安排备注 |

## 发票申请 InvoiceRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| request_no | string | 是 | 申请编号 |
| order_id | foreign_key | 否 | 关联订单 |
| customer_id | foreign_key | 是 | 客户 |
| invoice_type | enum | 是 | 普票、专票 |
| amount | decimal | 是 | 开票金额 |
| title | string | 是 | 发票抬头 |
| tax_number | string | 否 | 税号 |
| status | enum | 是 | 草稿、待审批、已通过、已驳回、已撤回 |
| applicant_id | user_id | 是 | 申请人 |
| approver_id | user_id | 否 | 审批人 |

## 付款申请 PaymentRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| request_no | string | 是 | 申请编号 |
| order_id | foreign_key | 否 | 关联订单 |
| customer_id | foreign_key | 否 | 客户 |
| payment_type | enum | 是 | 退款、采购、外协、其他 |
| payee | string | 是 | 收款方 |
| amount | decimal | 是 | 付款金额 |
| reason | text | 是 | 付款原因 |
| status | enum | 是 | 草稿、待审批、已通过、已驳回、已撤回 |
| applicant_id | user_id | 是 | 申请人 |
| approver_id | user_id | 否 | 审批人 |

## 售后申请 AfterSalesRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| request_no | string | 是 | 售后编号 |
| order_id | foreign_key | 是 | 关联订单 |
| type | enum | 是 | 退款、补发、返修、投诉、其他 |
| status | enum | 是 | 待受理、处理中、已完成、已关闭 |
| description | text | 是 | 问题描述 |
| solution | text | 否 | 处理方案 |
| refund_amount | decimal | 否 | 退款金额 |
| owner_id | user_id | 否 | 处理人 |

## 附件 Attachment

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file_name | string | 是 | 文件名 |
| file_url | string | 是 | 文件地址 |
| file_type | string | 是 | 文件类型 |
| file_size | integer | 是 | 文件大小 |
| business_type | enum | 是 | 订单、设计、生产、发票、付款、售后 |
| business_id | uuid | 是 | 关联业务 ID |
| uploader_id | user_id | 是 | 上传人 |

## 操作日志 OperationLog

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| actor_id | user_id | 是 | 操作人 |
| business_type | enum | 是 | 业务类型 |
| business_id | uuid | 是 | 业务 ID |
| action | string | 是 | 操作名称 |
| before_value | json | 否 | 操作前值 |
| after_value | json | 否 | 操作后值 |
| remark | text | 否 | 备注 |
