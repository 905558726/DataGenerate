# -*- coding: utf-8 -*-
"""
商品数据生成器
从预置商品库中采样/生成商品数据，补充模拟字段后输出 JSON 文件。
"""

import json
import sys
import os
import argparse
import random
from datetime import datetime, timedelta

# 添加 scripts 目录到 path 以导入 data_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_utils import (
    load_config, build_arg_parser, set_seed,
    random_float, random_int, random_datetime, generate_product_uuid,
)


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

    # 验证必填字段
    required_fields = ['name', 'brand', 'category', 'sub_category', 'price_min', 'price_max']
    for i, item in enumerate(library):
        for field in required_fields:
            if field not in item:
                print(f"[ERROR] Item {i} missing required field: {field}")
                sys.exit(1)

    return library


def generate_stock():
    """生成模拟库存：80% 100-9999, 15% 1-99, 5% 0"""
    r = random.random()
    if r < 0.05:
        return 0
    elif r < 0.20:
        return random_int(1, 99)
    else:
        return random_int(100, 9999)


def generate_sales_volume(stock):
    """生成模拟销量，与库存大致正相关"""
    if stock == 0:
        # 缺货商品也有可能有历史销量
        return random_int(0, 5000)
    elif stock < 100:
        base = stock * random_int(50, 200) // 100
        return max(0, base + random_int(-50, 200))
    else:
        # 正常库存：销量可以是库存的一定倍数
        ratio = random_float(0.3, 5.0, 1)
        return int(stock * ratio) + random_int(0, 1000)


def generate_description(item, is_variant=False, variant_suffix=""):
    """根据商品库条目生成商品描述"""
    brand = item.get('brand', '')
    name = item.get('name', '')
    category = item.get('sub_category', item.get('category', ''))
    keywords = item.get('keywords', [])

    # 组合关键词
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
    # 确保至少 10 个字符
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

    stock = generate_stock()
    sales_volume = generate_sales_volume(stock)

    name = item['name']
    if is_variant and variant_suffix:
        name = f"{item['name']} {variant_suffix}"

    product = {
        "product_id": generate_product_uuid(),
        "name": name,
        "brand": item.get('brand', ''),
        "category": item.get('category', ''),
        "sub_category": item.get('sub_category', ''),
        "price": price,
        "stock": stock,
        "description": generate_description(item, is_variant, variant_suffix),
        "image_url": item.get('image_url', f"https://picsum.photos/seed/{random.randint(1, 9999)}/400/400"),
        "keywords": item.get('keywords', []),
        "sales_volume": sales_volume,
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
        # 无放回随机采样
        sampled = random.sample(library, count)
        for item in sampled:
            product = generate_product(item, is_variant=False)
            products.append(product)
            seen_ids.add(product['product_id'])
    else:
        # 先用完整个库
        for item in library:
            product = generate_product(item, is_variant=False)
            products.append(product)
            seen_ids.add(product['product_id'])

        # 剩余数量用变体填充
        remaining = count - lib_size
        variant_count = 0
        max_attempts = remaining * 3  # 防止死循环
        attempts = 0

        while len(products) < count and attempts < max_attempts:
            attempts += 1
            item = random.choice(library)
            suffixes = item.get('variant_suffixes', [])
            deltas = item.get('variant_price_deltas', [])
            if not suffixes:
                # 没有预设变体，用简单的规格后缀
                suffixes = ["标准版", "升级版", "Pro版", "Lite版"]
                deltas = [0, 50, 100, -30]

            idx = random.randint(0, len(suffixes) - 1)
            suffix = suffixes[idx]
            delta = deltas[idx] if idx < len(deltas) else 0

            product = generate_product(item, is_variant=True, variant_suffix=suffix, variant_price_delta=delta)
            if product['product_id'] not in seen_ids:
                seen_ids.add(product['product_id'])
                products.append(product)
                variant_count += 1

        if len(products) < count:
            print(f"[WARNING] Only generated {len(products)}/{count} products (ran out of variants)")

    return products


def print_summary(products):
    """打印生成摘要"""
    print(f"\n{'='*60}")
    print(f"  商品生成摘要")
    print(f"{'='*60}")
    print(f"  总数量: {len(products)}")

    # 分类统计
    from collections import Counter
    cat_counter = Counter(p['category'] for p in products)
    is_variant_count = sum(1 for p in products if p.get('is_variant'))
    print(f"  变体数量: {is_variant_count}")
    print(f"  直采数量: {len(products) - is_variant_count}")
    print(f"  分类分布:")
    for cat, cnt in sorted(cat_counter.items(), key=lambda x: -x[1]):
        bar = '#' * min(cnt // max(1, len(products) // 20), 20)
        print(f"    {cat:8s}: {cnt:4d} {bar}")

    # 价格统计
    prices = [p['price'] for p in products]
    print(f"  价格区间: RMB{min(prices):.2f} ~ RMB{max(prices):.2f}")
    print(f"  平均价格: RMB{sum(prices)/len(prices):.2f}")

    # 库存统计
    stocks = [p['stock'] for p in products]
    zero_stock = sum(1 for s in stocks if s == 0)
    low_stock = sum(1 for s in stocks if 0 < s < 100)
    print(f"  缺货商品: {zero_stock}, 低库存: {low_stock}")

    # ID 唯一性
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
    parser.add_argument('--output', '-o', type=str, default=None, help='输出文件路径')
    parser.add_argument('--library', '-l', type=str, default=None, help='商品库文件路径')
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件路径')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    product_cfg = config.get('product', {})

    # 命令行参数优先
    count = args.count or product_cfg.get('count', 100)
    output_path = args.output or product_cfg.get('output_path', 'output/products.json')
    library_path = args.library or product_cfg.get('library_path', 'data/product_library.json')
    seed = args.seed if args.seed is not None else config.get('seed')

    # 设置随机种子
    if set_seed(seed):
        print(f"[INFO] 随机种子: {seed}")

    print(f"[INFO] 加载商品库: {library_path}")
    library = load_product_library(library_path)
    print(f"[INFO] 商品库条目数: {len(library)}")

    # 如果 count 为 0 或负数，用库大小
    if count <= 0:
        count = len(library)
        print(f"[INFO] count=0，使用库全部条目: {count}")

    print(f"[INFO] 目标生成数量: {count}")
    if count > len(library):
        print(f"[INFO] 请求数量 ({count}) > 库大小 ({len(library)})，将使用变体扩展")

    # 生成
    import time
    start = time.time()
    products = generate_products(library, count)
    elapsed = time.time() - start

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # 输出 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"\n[INFO] 输出文件: {output_path}")
    print(f"[INFO] 耗时: {elapsed:.2f} 秒")

    print_summary(products)


if __name__ == '__main__':
    main()
