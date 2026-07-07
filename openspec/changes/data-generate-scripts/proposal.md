## Why

在开发和测试电商系统时，经常需要大量真实感的中文电商测试数据（商品、订单等），手动构造数据耗时且难以保证多样性。经测试，京东等电商平台对搜索/列表页实施了严格的反爬策略（搜索接口连接超时、302 重定向封锁），实时抓取方案不可行。因此采用自建商品库方案——预置一个包含大量仿真实商品数据（品牌、名称、价格参考真实市场行情）的静态商品库，基于该库按需采样生成商品和订单数据。

## What Changes

- 新增商品库数据文件（`data/product_library.json`）：预置的仿真实商品库，涵盖多个品类、数百个商品条目（品牌名、商品名、价格参考真实市场），作为永久可复用的数据基座
- 新增商品数据生成脚本（`product_generator.py`）：从预置商品库中按指定数量采样/生成商品数据，补充库存、销量、描述等模拟字段，输出 JSON
- 新增订单数据生成脚本（`order_generator.py`）：依赖商品数据，生成包含买家、收货地址、支付、物流等完整信息的订单数据，输出 JSON
- 新增公共工具模块（`data_utils.py`）：提供随机化工具函数、中文数据字典（姓名、地址、手机号格式等）、配置加载与命令行解析
- 新增配置文件（`config.yaml`）：支持自定义数据量、输出路径、随机种子等参数
- 新增示例数据输出目录

## Capabilities

### New Capabilities

- `product-generator`: 商品数据生成器，从预置商品库中采样并按需补充模拟字段（库存、销量、描述等），按指定数量输出为 JSON
- `order-generator`: 订单数据生成器，基于已有商品数据生成订单，包括订单ID、关联商品明细、买家信息、收货地址、订单状态、支付信息、物流信息等字段，输出 JSON

### Modified Capabilities

<!-- 无现有能力修改 -->

## Impact

- 新增文件：`data/product_library.json`（预置商品库，静态数据）、`scripts/product_generator.py`、`scripts/order_generator.py`、`scripts/data_utils.py`、`config.yaml`
- 新增输出：`output/products.json`（生成的商品数据）、`output/orders.json`（生成的订单数据）
- 依赖：Python 3.8+，标准库（random, json, uuid, datetime），可选 `pyyaml` 用于 YAML 配置读取（无 pyyaml 时回退到 JSON 配置）
- 网络：无需网络，完全离线可用
