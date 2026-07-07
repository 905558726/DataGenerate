# -*- coding: utf-8 -*-
"""
订单数据生成器
基于已有商品数据生成完整订单（买家、收货地址、支付、物流）。
支持两种输出模式：
  - file:  --output output/orders.json       → JSON 文件
  - kafka: --output kafka://localhost:9092/orders → Kafka topic + 本地备份
"""

import json
import sys
import os
import argparse
import random
import time
from datetime import datetime, timedelta

# 添加 scripts 目录到 path 以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_utils import (
    load_config, set_seed,
    random_float, random_int, random_datetime, generate_order_id,
    generate_name, generate_phone, generate_email, generate_address,
    get_payment_method, get_logistics_company, generate_tracking_number,
    ORDER_REMARKS, weighted_choice,
)
from kafka_utils import parse_output_uri, KafkaOutputManager


def load_products(products_path):
    """加载商品数据"""
    if not os.path.exists(products_path):
        print(f"[ERROR] Products file not found: {products_path}")
        print("[TIP] Run product_generator.py first to generate products.")
        sys.exit(1)

    with open(products_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    if not isinstance(products, list) or len(products) == 0:
        print(f"[ERROR] Products file is empty or invalid: {products_path}")
        sys.exit(1)

    print(f"[INFO] 已加载 {len(products)} 个商品")
    return products


def select_order_items(products):
    """从商品池中选择订单明细项：1-5 个商品，quantity 加权分布"""
    num_items = weighted_choice([
        (1, 30),   # 30% 只买 1 件
        (2, 25),   # 25% 买 2 件
        (3, 20),   # 20% 买 3 件
        (4, 15),   # 15% 买 4 件
        (5, 10),   # 10% 买 5 件
    ])

    selected = random.sample(products, min(num_items, len(products)))

    items = []
    for product in selected:
        # quantity 加权分布
        quantity = weighted_choice([
            (1, 40), (2, 20), (3, 10),
            (4, 8), (5, 7), (6, 5),
            (7, 4), (8, 3), (9, 2), (10, 1),
        ])

        # 订单价格可以在商品库价格的 ±10% 范围内浮动，模拟促销/调价
        base_price = product['price']
        price_variance = random_float(-0.10, 0.10, 4)
        item_price = round(base_price * (1 + price_variance), 2)
        if item_price < 0.01:
            item_price = round(base_price, 2)

        subtotal = round(item_price * quantity, 2)

        items.append({
            "product_id": product['product_id'],
            "product_name": product['name'],
            "brand": product.get('brand', ''),
            "category": product.get('category', ''),
            "price": item_price,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return items


def generate_buyer():
    """生成买家信息"""
    return {
        "name": generate_name(),
        "phone": generate_phone(),
        "email": generate_email(),
    }


def generate_order_status():
    """按权重生成订单状态"""
    return weighted_choice([
        ("已完成", 50),
        ("已发货", 15),
        ("已付款", 15),
        ("待付款", 10),
        ("已取消", 10),
    ])


def generate_payment(status, order_amount, actual_amount):
    """生成支付信息，与订单状态一致"""
    method = get_payment_method()

    if status in ("已付款", "已发货", "已完成"):
        # 有支付时间
        paid_at = random_datetime(days_back=90).strftime("%Y-%m-%dT%H:%M:%S")
    else:
        # 待付款或已取消：无支付时间
        paid_at = None

    return {
        "method": method,
        "amount": actual_amount,
        "paid_at": paid_at,
    }


def generate_logistics(status, order_created_at):
    """生成物流信息，与订单状态一致"""
    company = get_logistics_company()

    if status in ("已发货", "已完成"):
        tracking_number = generate_tracking_number(company)
        # 发货时间在订单创建时间之后
        created_dt = datetime.strptime(order_created_at, "%Y-%m-%dT%H:%M:%S")
        shipped_at = created_dt + timedelta(hours=random_int(1, 48))
        # 预计送达在发货后 1-5 天
        estimated_delivery = shipped_at + timedelta(days=random_int(1, 5))
    else:
        tracking_number = None
        shipped_at = None
        estimated_delivery = None

    return {
        "company": company,
        "tracking_number": tracking_number,
        "shipped_at": shipped_at.strftime("%Y-%m-%dT%H:%M:%S") if shipped_at else None,
        "estimated_delivery": estimated_delivery.strftime("%Y-%m-%d") if estimated_delivery else None,
    }


def generate_order(products, date_range_days=90):
    """生成单条完整订单"""
    items = select_order_items(products)

    # 计算金额
    order_amount = round(sum(item['subtotal'] for item in items), 2)

    # 随机折扣：0 ~ 15%（整单折扣）
    discount_rate = weighted_choice([
        (0, 40),       # 40% 无折扣
        (0.05, 25),    # 25% 5% 折扣
        (0.10, 20),    # 20% 10% 折扣
        (0.15, 10),    # 10% 15% 折扣
        (0.20, 5),     # 5% 20% 折扣
    ])
    discount = round(order_amount * discount_rate, 2)
    actual_amount = round(order_amount - discount, 2)
    if actual_amount < 0.01:
        actual_amount = 0.01

    status = generate_order_status()

    # 如果已取消，实际支付金额为 0（退款）
    if status == "已取消":
        actual_amount = 0
        discount = order_amount

    created_at_dt = random_datetime(days_back=date_range_days)
    created_at = created_at_dt.strftime("%Y-%m-%dT%H:%M:%S")

    buyer = generate_buyer()
    shipping_address = generate_address()
    payment = generate_payment(status, order_amount, actual_amount)
    logistics = generate_logistics(status, created_at)

    # 备注：85% null，15% 有备注
    remark = None
    if random.random() < 0.15:
        remark = random.choice(ORDER_REMARKS)

    order = {
        "order_id": generate_order_id(),
        "items": items,
        "item_count": len(items),
        "buyer": buyer,
        "shipping_address": shipping_address,
        "order_status": status,
        "payment": payment,
        "logistics": logistics,
        "order_amount": order_amount,
        "discount": discount,
        "actual_amount": actual_amount,
        "created_at": created_at,
        "remark": remark,
    }

    return order


def generate_orders(products, count, date_range_days=90):
    """批量生成订单"""
    orders = []
    seen_ids = set()

    for i in range(count):
        # 重试机制：如果 order_id 重复则重新生成
        max_retries = 10
        for _ in range(max_retries):
            order = generate_order(products, date_range_days)
            if order['order_id'] not in seen_ids:
                break
            # 重新生成 order_id
            order['order_id'] = generate_order_id()

        seen_ids.add(order['order_id'])
        orders.append(order)

        if (i + 1) % max(1, count // 10) == 0:
            print(f"  进度: {i + 1}/{count}")

    return orders


def validate_orders(orders, products):
    """验证订单数据"""
    product_ids = {p['product_id'] for p in products}
    errors = []

    for order in orders:
        # 检查 items 中的 product_id 都在商品库中
        for item in order['items']:
            if item['product_id'] not in product_ids:
                errors.append(f"  Order {order['order_id']}: item {item['product_id']} not found in products")

        # 检查 order_amount 与 items subtotal 一致
        expected_amount = round(sum(item['subtotal'] for item in order['items']), 2)
        if abs(order['order_amount'] - expected_amount) > 0.02:
            errors.append(f"  Order {order['order_id']}: amount mismatch {order['order_amount']} vs {expected_amount}")

        # 检查 actual_amount = order_amount - discount
        expected_actual = round(order['order_amount'] - order['discount'], 2)
        if abs(order['actual_amount'] - expected_actual) > 0.02:
            errors.append(f"  Order {order['order_id']}: actual amount mismatch")

        # 状态一致性
        status = order['order_status']
        if status in ("已发货", "已完成"):
            if order['logistics']['tracking_number'] is None:
                errors.append(f"  Order {order['order_id']}: {status} but no tracking_number")
            if order['logistics']['shipped_at'] is None:
                errors.append(f"  Order {order['order_id']}: {status} but no shipped_at")
        if status in ("待付款",):
            if order['payment']['paid_at'] is not None:
                errors.append(f"  Order {order['order_id']}: {status} but payment.paid_at is set")
        if status == "已取消":
            if order['actual_amount'] != 0:
                errors.append(f"  Order {order['order_id']}: cancelled but actual_amount != 0")

    return errors


def print_summary(orders, output_mode='file'):
    """打印生成摘要"""
    print(f"\n{'='*60}")
    print(f"  订单生成摘要  (模式: {output_mode})")
    print(f"{'='*60}")
    print(f"  总数量: {len(orders)}")

    # 状态分布
    from collections import Counter
    status_counter = Counter(o['order_status'] for o in orders)
    print(f"  状态分布:")
    for status, cnt in sorted(status_counter.items(), key=lambda x: -x[1]):
        bar = '#' * (cnt * 20 // max(1, len(orders)))
        print(f"    {status:6s}: {cnt:4d} ({cnt*100//len(orders):2d}%) {bar}")

    # 金额统计
    amounts = [o['order_amount'] for o in orders]
    print(f"  订单金额区间: RMB{min(amounts):.2f} ~ RMB{max(amounts):.2f}")
    print(f"  平均订单金额: RMB{sum(amounts)/len(amounts):.2f}")

    # 平均每单商品数
    avg_items = sum(o['item_count'] for o in orders) / len(orders)
    print(f"  平均商品数/单: {avg_items:.1f}")

    # 支付方式分布
    pay_counter = Counter(o['payment']['method'] for o in orders)
    print(f"  支付方式分布:")
    for method, cnt in sorted(pay_counter.items(), key=lambda x: -x[1]):
        print(f"    {method}: {cnt} ({cnt*100//len(orders)}%)")

    # ID 唯一性
    ids = [o['order_id'] for o in orders]
    dupes = len(ids) - len(set(ids))
    if dupes > 0:
        print(f"  [WARNING] 发现 {dupes} 个重复 order_id！")
    else:
        print(f"  [OK] 所有 order_id 唯一")


def output_to_file(orders, file_path):
    """输出到 JSON 文件"""
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    return file_path


def output_to_kafka(orders, kafka_cfg, file_backup_path=None):
    """推送到 Kafka topic，同时可选本地备份"""
    host = kafka_cfg['host']
    port = kafka_cfg['port']
    topic = kafka_cfg['topic']

    manager = KafkaOutputManager(host, port, topic, file_backup_path)
    if not manager.connect():
        print("[WARN] Kafka 连接失败，仅写本地备份文件")
        if file_backup_path:
            output_to_file(orders, file_backup_path)
        return

    for order in orders:
        key = order['order_id']
        manager.send(key, order)

    manager.flush()
    stats = manager.get_stats()
    print(f"  Kafka 发送: {stats['success_count']} 成功, {stats['error_count']} 失败")
    manager.close()


def main():
    parser = argparse.ArgumentParser(description='订单数据生成器 - 基于商品数据生成订单')
    parser.add_argument('--count', '-n', type=int, default=None, help='生成订单数量')
    parser.add_argument('--seed', '-s', type=int, default=None, help='随机种子')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出目标: JSON文件路径 或 kafka://host:port/topic')
    parser.add_argument('--products', '-p', type=str, default=None, help='商品数据文件路径')
    parser.add_argument('--date-range', '-d', type=int, default=None, help='订单时间分布范围（天）')
    parser.add_argument('--file-backup', type=str, default=None,
                        help='Kafka模式下本地备份文件路径')
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件路径')
    parser.add_argument('--skip-validation', action='store_true', help='跳过数据验证')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    order_cfg = config.get('order', {})
    kafka_cfg = config.get('kafka', {})

    # 命令行参数优先
    count = args.count or order_cfg.get('count', 50)
    output_arg = args.output or order_cfg.get('output_path', 'output/orders.json')
    products_path = args.products or order_cfg.get('products_path', 'output/products.json')
    date_range_days = args.date_range or order_cfg.get('date_range_days', 90)
    seed = args.seed if args.seed is not None else config.get('seed')

    # 解析输出模式
    output_mode, output_config = parse_output_uri(output_arg)

    # 设置随机种子
    if set_seed(seed):
        print(f"[INFO] 随机种子: {seed}")

    print(f"[INFO] 加载商品数据: {products_path}")
    products = load_products(products_path)

    print(f"[INFO] 目标生成数量: {count}, 输出模式: {output_mode}")
    print(f"[INFO] 日期范围: 近 {date_range_days} 天")

    # 生成
    start = time.time()
    orders = generate_orders(products, count, date_range_days)
    elapsed = time.time() - start

    # 验证
    if not args.skip_validation:
        print(f"\n[INFO] 验证订单数据...")
        errors = validate_orders(orders, products)
        if errors:
            print(f"[WARNING] 发现 {len(errors)} 个问题:")
            for e in errors[:10]:
                print(e)
        else:
            print(f"  [OK] 数据验证通过")

    # 输出
    if output_mode == 'kafka':
        file_backup = args.file_backup
        if not file_backup and kafka_cfg.get('file_backup', True):
            backup_dir = kafka_cfg.get('file_backup_dir', 'output')
            file_backup = os.path.join(backup_dir, f"orders_{output_config['topic']}_backup.json")
        print(f"[INFO] 推送到 Kafka: {output_config['host']}:{output_config['port']}/{output_config['topic']}")
        output_to_kafka(orders, output_config, file_backup)
    else:
        file_path = output_config['path']
        output_to_file(orders, file_path)
        print(f"\n[INFO] 输出文件: {file_path}")

    print(f"[INFO] 耗时: {elapsed:.2f} 秒")

    print_summary(orders, output_mode)


if __name__ == '__main__':
    main()
