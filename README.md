# DataGenerate - 中文电商模拟数据生成工具

基于预置商品库的 Python 数据生成工具，一键生成符合中文电商场景的商品和订单模拟数据（JSON 格式）。

## 快速开始

```bash
# 1. 生成商品数据（100 条）
python scripts/product_generator.py --count 100

# 2. 基于商品数据生成订单（50 条）
python scripts/order_generator.py --count 50
```

生成的 JSON 文件位于 `output/` 目录下。

## 项目结构

```
DataGenerate/
├── config.yaml                    # 默认配置文件（商品/订单数量、输出路径、随机种子）
├── data/
│   └── product_library.json       # 预置商品库（8大品类，187+条参考真实行情商品）
├── scripts/
│   ├── __init__.py
│   ├── data_utils.py              # 公共工具模块（中文姓名/手机/邮箱/地址生成器、随机函数）
│   ├── product_generator.py       # 商品生成器（采样+变体扩展+模拟字段）
│   └── order_generator.py         # 订单生成器（完整订单+买家+地址+支付+物流）
├── output/
│   ├── .gitkeep
│   ├── products.json              # 商品数据输出
│   └── orders.json                # 订单数据输出
└── openspec/                      # OpenSpec 方案文档
    └── changes/data-generate-scripts/
        ├── proposal.md            # 需求提案
        ├── design.md              # 技术设计
        ├── specs/                 # 规格说明
        └── tasks.md               # 任务清单
```

## 功能特性

- **纯离线运行**：无网络依赖，无强制第三方库（pyyaml 可选，无安装时回退 JSON 配置）
- **真实感商品库**：8 大品类（电子产品、服装、食品饮料、家居生活、美妆个护、母婴、运动户外、图书文娱），品牌/品名/价格参考真实市场行情
- **智能变体扩展**：请求数量超过库大小时自动生成不同规格/颜色/容量变体
- **完整订单生成**：买家信息、收货地址（省市区三级联动）、支付信息、物流信息、订单状态，所有字段状态逻辑一致
- **可复现**：支持 `--seed` 固定随机种子，两次运行输出完全一致
- **数据校验**：订单生成后自动校验 product_id 引用有效性、金额一致性、状态-支付-物流一致性

## 依赖

- Python 3.8+
- 可选：`pyyaml`（用于 YAML 配置，无安装时自动回退 JSON）

```bash
pip install pyyaml  # 可选
```

## 配置

编辑 `config.yaml` 修改默认参数：

```yaml
product:
  count: 100                  # 默认生成商品数量
  output_path: "output/products.json"
  library_path: "data/product_library.json"

order:
  count: 50                   # 默认生成订单数量
  output_path: "output/orders.json"
  products_path: "output/products.json"
  date_range_days: 90         # 订单时间分布范围

seed: null                    # 随机种子（null = 不固定）
```

## 命令行参数

### 商品生成器 (product_generator.py)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count, -n` | 生成商品数量 | config.yaml 中的值 |
| `--seed, -s` | 随机种子（固定后结果可复现） | config.yaml 中的值 |
| `--output, -o` | 输出文件路径 | config.yaml 中的值 |
| `--library, -l` | 商品库文件路径 | config.yaml 中的值 |
| `--config, -c` | 配置文件路径 | config.yaml |

示例：

```bash
# 生成 500 个商品
python scripts/product_generator.py --count 500

# 固定种子 + 自定义输出路径
python scripts/product_generator.py --count 200 --seed 42 --output data/my_products.json
```

### 订单生成器 (order_generator.py)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count, -n` | 生成订单数量 | config.yaml 中的值 |
| `--seed, -s` | 随机种子 | config.yaml 中的值 |
| `--output, -o` | 输出文件路径 | config.yaml 中的值 |
| `--products, -p` | 商品数据文件路径 | config.yaml 中的值 |
| `--date-range, -d` | 订单时间分布范围（天） | 90 |
| `--skip-validation` | 跳过数据验证 | false |

示例：

```bash
# 生成 200 个订单，时间范围为近 30 天
python scripts/order_generator.py --count 200 --date-range 30

# 从指定商品文件生成订单
python scripts/order_generator.py --products output/my_products.json --count 1000
```

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
