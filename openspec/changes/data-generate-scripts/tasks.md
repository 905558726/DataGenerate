# Tasks: Data Generate Scripts

## 1. 项目基础搭建

- [ ] 1.1 创建项目目录结构（`scripts/`、`data/`、`output/`）和空白 `__init__.py` 文件
- [ ] 1.2 创建 `requirements.txt`，标注 Python >= 3.8 及可选依赖（pyyaml, kafka-python）
- [ ] 1.3 创建 `config.yaml` 配置文件，包含：商品/订单生成数量、输出路径、输出模式（file/kafka）、Kafka 连接参数、随机种子
- [ ] 1.4 创建 `output/.gitkeep` 确保输出目录被 git 跟踪

## 2. 预置商品库 (data/product_library.json)

- [ ] 2.1 构建商品库框架：确定 JSON Schema，每个条目包含 name, brand, category, sub_category, price_min, price_max, image_url, keywords, variant_suffixes
- [ ] 2.2 填充"电子产品"分类商品（手机、笔记本电脑、平板、耳机、智能手表等，40-50 条，价格参考真实行情）
- [ ] 2.3 填充"服装"分类商品（男装、女装、童装、内衣等，40-50 条）
- [ ] 2.4 填充"食品饮料"分类商品（休闲零食、饮料冲调、生鲜水果、粮油调味、酒类等，30-40 条）
- [ ] 2.5 填充"家居生活"分类商品（家纺、厨具、家具、收纳用品、灯具等，30-40 条）
- [ ] 2.6 填充"美妆个护"分类商品（护肤、彩妆、洗护、口腔护理、男士护理等，30-40 条）
- [ ] 2.7 填充"母婴"分类商品（奶粉辅食、纸尿裤、童车童床、孕产用品等，20-30 条）
- [ ] 2.8 填充"运动户外"分类商品（运动鞋、健身器材、户外装备、骑行等，20-30 条）
- [ ] 2.9 填充"图书文娱"分类商品（小说、教辅、少儿图书、文具、玩具等，20-30 条）
- [ ] 2.10 验证商品库：确认 JSON 格式正确、无重复名称、category 一致性、条目总数≥180

## 3. 公共工具模块 (data_utils.py)

- [ ] 3.1 实现中文姓名生成器（姓氏列表 + 名字列表，支持单姓/复姓，性别区分）
- [ ] 3.2 实现手机号生成器（符合中国手机号格式：1[3-9]xxxxxxxxx）
- [ ] 3.3 实现邮箱生成器（基于姓名拼音首字母 + 常见邮箱域名 @qq.com/@163.com/@gmail.com）
- [ ] 3.4 实现收货地址生成器（省市区三级联动真实数据 + 详细地址随机模板 + 6 位邮编匹配城市）
- [ ] 3.5 实现支付方式列表和物流公司列表的数据字典（含运单号前缀规则）
- [ ] 3.6 实现通用随机工具函数：加权随机选择、范围内的随机浮点/整数、随机日期时间、UUID/短ID 生成
- [ ] 3.7 实现配置加载 + 命令行解析函数：优先 yaml，回退 json；支持 --count, --seed, --output, --library, --products 等公共参数
- [ ] 3.8 实现输出 URI 解析函数：解析 `kafka://host:port/topic` 格式，区分为 file/kafka 模式

## 4. Kafka 工具模块 (kafka_utils.py)

- [ ] 4.1 实现 Kafka 生产者连接工厂函数（解析 broker 地址、超时配置、连接重试）
- [ ] 4.2 实现消息发送函数 `send_to_kafka(producer, topic, key, value)`：JSON 序列化 + 异步发送 + 错误重试
- [ ] 4.3 实现批量推送管理器 `KafkaOutputManager`：管理 producer 生命周期，支持 `--kafka-batch-size` 批量发送
- [ ] 4.4 实现 `resolve_output_mode(output_arg)` 函数：解析 --output 参数，返回 `(mode, config_dict)`

## 5. 商品生成器 (product_generator.py)

- [ ] 5.1 实现商品库加载与验证函数（检查必填字段、分类统计、数量下限检查）
- [ ] 5.2 实现单条商品生成函数：从库条目采样 → 决定是否生成变体 → 生成全部字段
- [ ] 5.3 实现变体生成逻辑：variant_suffixes 随机选取 + 价格微调 + is_variant=true
- [ ] 5.4 实现模拟字段生成：stock（80%:100-9999, 15%:1-99, 5%:0），sales_volume，description（品牌+名称+关键词拼接）
- [ ] 5.5 实现采样策略：count ≤ 库大小无放回采样；count > 库大小全量采样 + 变体扩展
- [ ] 5.6 实现 product_id 唯一性校验
- [ ] 5.7 实现双模式输出控制器：file 模式写 JSON 数组 → kafka 模式逐条推送到 topic
- [ ] 5.8 实现 `main()` 入口：解析参数 → 解析 output URI → 加载商品库 → 生成 → 输出（file/kafka）→ 打印摘要

## 6. 订单生成器 (order_generator.py)

- [ ] 6.1 实现商品 JSON 文件加载函数（支持 `--products` 指定路径）
- [ ] 6.2 实现 `select_order_items(products)` 函数：随机选取 1-5 个商品 + quantity 加权分布
- [ ] 6.3 实现 `generate_buyer()` 买家信息生成（复用 data_utils）
- [ ] 6.4 实现 `generate_shipping_address()` 收货地址生成（复用 data_utils）
- [ ] 6.5 实现订单状态按权重分配（已完成 50%、已发货 15%、已付款 15%、待付款 10%、已取消 10%）
- [ ] 6.6 实现支付信息生成 + paid_at 状态一致性校验
- [ ] 6.7 实现物流信息生成 + shipped_at/tracking_number 状态一致性校验
- [ ] 6.8 实现订单金额计算（subtotal 求和 → order_amount → discount → actual_amount）
- [ ] 6.9 实现订单备注随机生成（85% null，15% 随机备注）
- [ ] 6.10 实现单条订单完整生成 + order_id 唯一性校验
- [ ] 6.11 实现批量生成 + 时间分布（默认近 90 天）
- [ ] 6.12 实现双模式输出控制器：file 模式写 JSON → kafka 模式逐条推送到 topic
- [ ] 6.13 实现 `main()` 入口：解析参数 → 解析 output URI → 加载商品 → 生成 → 输出 → 打印摘要

## 7. 集成和验证

- [ ] 7.1 端到端 File 模式：product_generator.py --count 100 → order_generator.py --count 50 → 检查 JSON 完整性
- [ ] 7.2 验证商品 JSON：12 个字段完整、product_id 无重复、is_variant 标记正确
- [ ] 7.3 验证订单 JSON：字段完整、order_id 无重复、product_id 引用有效、状态-支付-物流一致性
- [ ] 7.4 测试 `--seed` 可复现性：同种子两次运行输出完全一致
- [ ] 7.5 测试变体生成：count > 库条目数时确认 ID 唯一、变体正确
- [ ] 7.6 测试 Kafka 模式：product_generator.py --output kafka://localhost:9092/test_products --count 10
- [ ] 7.7 测试 Kafka 不可达时的错误处理和本地备份文件
- [ ] 7.8 测试 `--count`、`--output`、`--library` 等命令行参数以及 config.yaml 配置回退逻辑
