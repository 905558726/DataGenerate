# DataGenerate - 中文电商模拟数据生成工具

基于预置商品库的 Python 数据生成工具，一键生成符合中文电商场景的商品和订单模拟数据。支持 **JSON 文件**和 **Kafka 生产者推送**两种输出模式。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

> 提示：`pyyaml` 和 `kafka-python` 为可选依赖。无 pyyaml 时自动回退 JSON 配置；仅在 Kafka 模式下需要 kafka-python。

### File 模式（输出 JSON 文件）

```bash
# 1. 生成商品数据（100 条）
python scripts/product_generator.py --count 100

# 2. 基于商品数据生成订单（50 条）
python scripts/order_generator.py --count 50
```

生成的 JSON 文件位于 `output/` 目录下。

### Kafka 模式（推送到 Kafka Topic）

```bash
# 商品数据推送到 Kafka（同时写本地备份文件）
python scripts/product_generator.py --output kafka://localhost:9092/products --count 100

# 订单数据推送到 Kafka
python scripts/order_generator.py --output kafka://localhost:9092/orders --count 50
```

Kafka URI 格式：`kafka://host:port/topic`，程序会自动识别协议切换到 Kafka 输出模式。Kafka 模式下每条数据作为独立 JSON 消息发送，同时自动生成本地 JSON 备份文件。

## 项目结构

```
DataGenerate/
├── config.yaml                    # 默认配置文件（输出模式、数据量、Kafka 参数等）
├── requirements.txt               # Python 依赖
├── README.md
├── data/
│   └── product_library.json       # 预置商品库（8大品类，187+条参考真实行情商品）
├── scripts/
│   ├── __init__.py
│   ├── data_utils.py              # 公共工具（中文姓名/手机/邮箱/地址生成器、随机函数）
│   ├── kafka_utils.py             # Kafka 工具（生产者连接、消息发送、连接管理）
│   ├── product_generator.py       # 商品生成器（file/kafka 双模式）
│   └── order_generator.py         # 订单生成器（file/kafka 双模式）
├── output/                        # 数据输出目录
└── openspec/                      # OpenSpec 方案文档
    └── changes/data-generate-scripts/
        ├── proposal.md            # 需求提案
        ├── design.md              # 技术设计
        ├── specs/                 # 规格说明
        └── tasks.md               # 任务清单
```

## 功能特性

- **双输出模式**：`--output` 参数自动识别 `file` 模式（JSON 文件路径）和 `kafka` 模式（`kafka://host:port/topic` URI）
- **Kafka 本地备份**：Kafka 模式下自动写本地 JSON 备份文件，防数据丢失
- **纯离线可用**：File 模式零网络依赖，零强制第三方库
- **真实感商品库**：8 大品类（电子产品、服装、食品饮料、家居生活、美妆个护、母婴、运动户外、图书文娱），品牌/品名/价格参考真实市场行情
- **智能变体扩展**：请求数量超过库大小时自动生成不同规格/颜色/容量变体
- **完整订单生成**：买家信息、收货地址（省市区三级联动）、支付信息、物流信息、订单状态，所有字段状态逻辑一致
- **可复现**：支持 `--seed` 固定随机种子，两次运行输出完全一致
- **数据校验**：订单生成后自动校验 product_id 引用有效性、金额一致性、状态-支付-物流一致性

## 依赖

| 依赖 | 是否必需 | 说明 |
|------|---------|------|
| Python 3.8+ | 必需 | 核心语言版本 |
| pyyaml >= 6.0 | 可选 | YAML 配置增强，无安装时自动回退 JSON |
| kafka-python >= 2.0 | 可选 | 仅在 `--output kafka://...` 模式时需要 |

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml` 修改默认参数：

```yaml
product:
  count: 100                                    # 默认生成商品数量
  output_path: "output/products.json"            # 输出路径（file 或 kafka://host:port/topic）
  library_path: "data/product_library.json"      # 预置商品库路径

order:
  count: 50                                     # 默认生成订单数量
  output_path: "output/orders.json"             # 输出路径（file 或 kafka://host:port/topic）
  products_path: "output/products.json"          # 依赖的商品数据文件
  date_range_days: 90                            # 订单时间分布范围（天）

kafka:
  batch_size: 1                                  # 批量发送大小，1=逐条
  connection_timeout: 10                          # 连接超时（秒）
  file_backup: true                               # Kafka 模式是否写本地 JSON 备份
  file_backup_dir: "output"                       # 本地备份文件目录

seed: null                                        # 随机种子（null = 不固定）
```

## 命令行参数

### 商品生成器 (product_generator.py)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count, -n` | 生成商品数量 | config.yaml |
| `--seed, -s` | 随机种子 | config.yaml |
| `--output, -o` | 输出目标：文件路径 或 `kafka://host:port/topic` | config.yaml |
| `--library, -l` | 商品库文件路径 | config.yaml |
| `--file-backup` | Kafka 模式下本地备份文件路径 | 自动生成 |
| `--config, -c` | 配置文件路径 | config.yaml |

示例：

```bash
# File 模式：生成 500 个商品到指定文件
python scripts/product_generator.py --count 500 --output output/my_products.json

# Kafka 模式：推送到指定 topic，同时写本地备份
python scripts/product_generator.py --output kafka://192.168.1.100:9092/products --count 1000

# 使用自定义端口
python scripts/product_generator.py --output kafka://localhost:9093/products --count 100
```

### 订单生成器 (order_generator.py)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count, -n` | 生成订单数量 | config.yaml |
| `--seed, -s` | 随机种子 | config.yaml |
| `--output, -o` | 输出目标：文件路径 或 `kafka://host:port/topic` | config.yaml |
| `--products, -p` | 商品数据文件路径 | config.yaml |
| `--date-range, -d` | 订单时间分布范围（天） | config.yaml |
| `--file-backup` | Kafka 模式下本地备份文件路径 | 自动生成 |
| `--skip-validation` | 跳过数据验证 | false |
| `--config, -c` | 配置文件路径 | config.yaml |

示例：

```bash
# File 模式
python scripts/order_generator.py --count 200 --date-range 30

# Kafka 模式
python scripts/order_generator.py --output kafka://localhost:9092/orders --count 500

# Kafka 模式 + 自定义备份路径
python scripts/order_generator.py --output kafka://localhost:9092/orders --file-backup data/backup_orders.json --count 1000
```

## 输出模式对比

| 特性 | File 模式 | Kafka 模式 |
|------|---------|-----------|
| `--output` 格式 | `path/to/file.json` | `kafka://host:port/topic` |
| 数据格式 | JSON 数组（一次性写入） | 逐条 JSON 消息 |
| 网络依赖 | 无 | 需连接 Kafka Broker |
| 额外依赖 | 无 | `kafka-python` |
| 本地备份 | 就是本地文件 | 默认自动备份 |
| 适用场景 | 离线开发/测试 | 实时数据流/集成测试 |

## 数据格式

### 商品数据 (products.json)

```json
{
  "product_id": "a1b2c3d4-...",
  "name": "iPhone 15 Pro Max 256GB",
  "brand": "Apple",
  "category": "电子产品",
  "sub_category": "手机",
  "price": 9999.00,
  "stock": 1500,
  "description": "Apple iPhone 15 Pro Max 256GB，手机类热销商品...",
  "image_url": "https://picsum.photos/seed/iphone15pm/400/400",
  "keywords": ["5G手机", "旗舰", "大屏", "拍照"],
  "sales_volume": 28500,
  "created_at": "2026-05-12T10:30:00",
  "is_variant": false
}
```

### 订单数据 (orders.json)

```json
{
  "order_id": "ORD20260707143052001",
  "items": [{
    "product_id": "a1b2c3d4-...",
    "product_name": "iPhone 15 Pro Max 256GB",
    "brand": "Apple",
    "category": "电子产品",
    "price": 9899.00,
    "quantity": 1,
    "subtotal": 9899.00
  }],
  "item_count": 2,
  "buyer": {
    "name": "王伟",
    "phone": "13800138000",
    "email": "py_xkjsdf@qq.com"
  },
  "shipping_address": {
    "province": "广东省",
    "city": "深圳市",
    "district": "南山区",
    "detail": "科技路128号",
    "postal_code": "518051",
    "recipient_name": "王伟",
    "recipient_phone": "13800138000"
  },
  "order_status": "已完成",
  "payment": {
    "method": "微信支付",
    "amount": 11489.00,
    "paid_at": "2026-07-05T14:30:00"
  },
  "logistics": {
    "company": "顺丰速运",
    "tracking_number": "SF1234202407010001",
    "shipped_at": "2026-07-05T16:00:00",
    "estimated_delivery": "2026-07-08"
  },
  "order_amount": 11689.00,
  "discount": 200.00,
  "actual_amount": 11489.00,
  "created_at": "2026-07-05T14:30:00",
  "remark": null
}
```

## 预置商品库品类

| 品类 | 子类 | 商品数 |
|------|------|--------|
| 电子产品 | 手机、笔记本电脑、平板、耳机、智能手表 | 52 |
| 服装 | 男装、女装、童装、内衣 | 30 |
| 食品饮料 | 休闲零食、饮料冲调、生鲜水果、粮油调味、酒类 | 20 |
| 家居生活 | 家纺、厨具、家具、收纳用品、灯具 | 18 |
| 美妆个护 | 护肤、彩妆、洗护、口腔护理、男士护理 | 21 |
| 母婴 | 奶粉辅食、纸尿裤、童车童床、孕产用品 | 11 |
| 运动户外 | 运动鞋、健身器材、户外装备、骑行 | 18 |
| 图书文娱 | 小说、教辅、少儿图书、文具、玩具 | 17 |

## 订单状态逻辑

| 状态 | 支付 | 物流 | 实际金额 |
|------|------|------|----------|
| 待付款 | 已选支付方式，未付 | 无物流 | = 订单金额 |
| 已付款 | 已支付 | 无物流 | = 订单金额 - 折扣 |
| 已发货 | 已支付 | 已发货（含物流单号） | = 订单金额 - 折扣 |
| 已完成 | 已支付 | 已签收 | = 订单金额 - 折扣 |
| 已取消 | 未付 | 无物流 | 0 |
