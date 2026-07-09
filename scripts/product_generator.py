#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品数据生成器
从预置商品库中采样/生成商品数据，补充模拟字段后输出。
支持两种输出模式：
  - file:  --output output/products.json       → JSON 文件
  - kafka: --output kafka://localhost:9092/products → Kafka topic + 本地备份
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
    random_float, random_int, random_datetime, generate_product_uuid,
)
from kafka_utils import parse_output_uri, KafkaOutputManager


def load_product_library(library_path):
    """加载预置商品库并验证"""
    if not os.path.exists(library_path):
        print(f"[ERROR] Product library not found: {library_path}")
        print("[TIP] Please ensure data/product_library.json exists.")
        sys.exit(1)

    with open(library_path, 'r', encoding='utf-8') as f:
        library = json.load(f)

    if not isinstance(library, list) or len(library) == 0:
        print(f"[ERROR] Product library is empty or invalid: {library_path}")
        sys.exit(1)

    required_fields = ['name', 'brand', 'category', 'sub_category', 'price_min', 'price_max']
    for i, item in enumerate(library):
        for field in required_fields:
            if field not in item:
                print(f"[ERROR] Item {i} missing required field: {field}")
                sys.exit(1)

    return library


def generate_description(item, is_variant=False, variant_suffix=""):
    """根据商品库条目生成商品描述"""
    brand = item.get('brand', '')
    name = item.get('name', '')
    category = item.get('sub_category', item.get('category', ''))
    keywords = item.get('keywords', [])
    kw_text = '、'.join(random.sample(keywords, min(3, len(keywords)))) if keywords else ''

    name_with_variant = name
    if is_variant and variant_suffix:
        name_with_variant = name + ' ' + variant_suffix

    templates = [
        f"{brand} {name_with_variant}，{category}类热销商品，{kw_text}，品质保证，值得信赖。",
        f"【{brand}官方正品】{name_with_variant}，{kw_text}，{category}精选好物，全国联保，售后无忧。",
        f"{name_with_variant}由{brand}出品，{category}品类中的明星产品，{kw_text}，深受消费者喜爱。",
        f"{brand} {name_with_variant}，{kw_text}，{category}畅销单品，质量可靠，口碑之选。",
        f"{name_with_variant}，{brand}旗下{category}力作，{kw_text}，性价比超高，好评如潮。",
    ]

    desc = random.choice(templates)
    if len(desc) < 10:
        desc = f"{brand} {name_with_variant}，{kw_text}，{category}热销商品。" if kw_text else f"{brand} {name_with_variant}，{category}热销推荐商品，正品保证。"
    return desc


def generate_product(item, is_variant=False, variant_suffix="", variant_price_delta=0):
    """从商品库条目生成单条商品记录"""
    price = random_float(item['price_min'], item['price_max'])
    if is_variant:
        price = round(price + variant_price_delta, 2)
        if price < item['price_min'] * 0.9:
            price = random_float(item['price_min'], item['price_max'])

    name = item['name']
    if is_variant and variant_suffix:
        name = f"{item['name']} {variant_suffix}"

    # 使用商品库中预置的 product_id，变体才生成新 ID
    pid = item.get('product_id')
    if not pid or is_variant:
        pid = generate_product_uuid()

    product = {
        "product_id": pid,
        "name": name,
        "brand": item.get('brand', ''),
        "category": item.get('category', ''),
        "sub_category": item.get('sub_category', ''),
        "price": price,
        "description": generate_description(item, is_variant, variant_suffix),
        "image_url": item.get('image_url', f"https://picsum.photos/seed/{random.randint(1, 9999)}/400/400"),
        "keywords": item.get('keywords', []),
        "created_at": random_datetime(days_back=365).strftime("%Y-%m-%dT%H:%M:%S"),
        "is_variant": is_variant,
    }
    return product


def generate_products(library, count):
    """从商品库生成指定数量的商品"""
    products = []
    seen_ids = set()
    lib_size = len(library)

    if count <= lib_size:
        sampled = random.sample(library, count)
        for item in sampled:
            product = generate_product(item, is_variant=False)
            products.append(product)
            seen_ids.add(product['product_id'])
    else:
        for item in library:
            product = generate_product(item, is_variant=False)
            products.append(product)
            seen_ids.add(product['product_id'])

        remaining = count - lib_size
        max_attempts = remaining * 3
        attempts = 0

        while len(products) < count and attempts < max_attempts:
            attempts += 1
            item = random.choice(library)
            suffixes = item.get('variant_suffixes', [])
            deltas = item.get('variant_price_deltas', [])
            if not suffixes:
                suffixes = ["标准版", "升级版", "Pro版", "Lite版"]
                deltas = [0, 50, 100, -30]

            idx = random.randint(0, len(suffixes) - 1)
            suffix = suffixes[idx]
            delta = deltas[idx] if idx < len(deltas) else 0

            product = generate_product(item, is_variant=True, variant_suffix=suffix, variant_price_delta=delta)
            if product['product_id'] not in seen_ids:
                seen_ids.add(product['product_id'])
                products.append(product)

        if len(products) < count:
            print(f"[WARNING] Only generated {len(products)}/{count} products (ran out of variants)")

    return products


def output_to_file(products, file_path):
    """输出到 JSON 文件"""
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    return file_path


def output_to_kafka(products, kafka_cfg, file_backup_path=None, file_output_path=None):
    """推送到 Kafka topic，同时可选本地备份 + 始终写一份 JSON 供 order_generator 使用"""
    # 始终写一份标准 JSON 文件（order_generator 依赖此文件）
    if file_output_path:
        output_to_file(products, file_output_path)

    host = kafka_cfg['host']
    port = kafka_cfg['port']
    topic = kafka_cfg['topic']

    manager = KafkaOutputManager(host, port, topic, file_backup_path)
    if not manager.connect():
        print("[WARN] Kafka 连接失败，仅写本地备份文件")
        if file_backup_path:
            output_to_file(products, file_backup_path)
        return

    for product in products:
        key = product['product_id']
        manager.send(key, product)

    manager.flush()
    stats = manager.get_stats()
    print(f"  Kafka 发送: {stats['success_count']} 成功, {stats['error_count']} 失败")
    manager.close()


def print_summary(products, output_mode='file'):
    """打印生成摘要"""
    print(f"\n{'='*60}")
    print(f"  商品生成摘要  (模式: {output_mode})")
    print(f"{'='*60}")
    print(f"  总数量: {len(products)}")

    from collections import Counter
    cat_counter = Counter(p['category'] for p in products)
    is_variant_count = sum(1 for p in products if p.get('is_variant'))
    print(f"  变体数量: {is_variant_count}")
    print(f"  直采数量: {len(products) - is_variant_count}")
    print(f"  分类分布:")
    for cat, cnt in sorted(cat_counter.items(), key=lambda x: -x[1]):
        bar = '#' * min(cnt // max(1, len(products) // 20), 20)
        print(f"    {cat:8s}: {cnt:4d} {bar}")

    prices = [p['price'] for p in products]
    print(f"  价格区间: RMB{min(prices):.2f} ~ RMB{max(prices):.2f}")
    print(f"  平均价格: RMB{sum(prices)/len(prices):.2f}")

    ids = [p['product_id'] for p in products]
    dupes = len(ids) - len(set(ids))
    if dupes > 0:
        print(f"  [WARNING] 发现 {dupes} 个重复 product_id！")
    else:
        print(f"  [OK] 所有 product_id 唯一")


def main():
    parser = argparse.ArgumentParser(description='商品数据生成器 - 从预置商品库采样生成')
    parser.add_argument('--count', '-n', type=int, default=None, help='生成商品数量')
    parser.add_argument('--seed', '-s', type=int, default=None, help='随机种子')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出目标: JSON文件路径 或 kafka://host:port/topic')
    parser.add_argument('--library', '-l', type=str, default=None, help='商品库文件路径')
    parser.add_argument('--file-backup', type=str, default=None,
                        help='Kafka模式下本地备份文件路径（默认自动生成）')
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件路径')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    product_cfg = config.get('product', {})
    kafka_cfg = config.get('kafka', {})

    # 命令行参数优先
    count = args.count or product_cfg.get('count', 100)
    output_arg = args.output or product_cfg.get('output_path', 'output/products.json')
    library_path = args.library or product_cfg.get('library_path', 'data/product_library.json')
    seed = args.seed if args.seed is not None else config.get('seed')

    # 解析输出模式
    output_mode, output_config = parse_output_uri(output_arg)

    if set_seed(seed):
        print(f"[INFO] 随机种子: {seed}")

    print(f"[INFO] 加载商品库: {library_path}")
    library = load_product_library(library_path)
    print(f"[INFO] 商品库条目数: {len(library)}")

    if count <= 0:
        count = len(library)

    print(f"[INFO] 目标生成数量: {count}, 输出模式: {output_mode}")
    if count > len(library):
        print(f"[INFO] 请求数量 ({count}) > 库大小 ({len(library)})，将使用变体扩展")

    # 生成
    start = time.time()
    products = generate_products(library, count)
    elapsed = time.time() - start

    # 输出
    if output_mode == 'kafka':
        # 始终写一份标准 products.json 供 order_generator 使用
        default_file = product_cfg.get('output_path', 'output/products.json')
        if not args.file_backup and not args.output.startswith('kafka://'):
            default_file = args.output
        file_backup = args.file_backup
        if not file_backup and kafka_cfg.get('file_backup', True):
            backup_dir = kafka_cfg.get('file_backup_dir', 'output')
            file_backup = os.path.join(backup_dir, f"products_{output_config['topic']}_backup.json")
        print(f"[INFO] 推送到 Kafka: {output_config['host']}:{output_config['port']}/{output_config['topic']}")
        output_to_kafka(products, output_config, file_backup, file_output_path=default_file)
        print(f"\n[INFO] 已同步写出商品文件: {default_file}")
    else:
        file_path = output_config['path']
        output_to_file(products, file_path)
        print(f"\n[INFO] 输出文件: {file_path}")

    print(f"[INFO] 耗时: {elapsed:.2f} 秒")
    print_summary(products, output_mode)


if __name__ == '__main__':
    main()
