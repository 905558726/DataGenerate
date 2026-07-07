#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共工具模块：中文数据字典、随机生成函数、配置加载、命令行参数解析
"""

import random
import json
import uuid
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 尝试加载 YAML，失败则回退 JSON
# ============================================================
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def load_config(config_path="config.yaml"):
    """加载配置文件，优先 YAML，无 pyyaml 时回退 JSON"""
    path = Path(config_path)
    if not path.exists():
        print(f"[WARNING] Config file not found: {config_path}, using defaults")
        return {}

    if _HAS_YAML and path.suffix in ('.yaml', '.yml'):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    elif path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif path.suffix in ('.yaml', '.yml'):
        # No YAML lib, try reading as JSON anyway (simple YAML can parse as JSON)
        print("[WARNING] pyyaml not installed, trying JSON fallback for config")
        # Try reading a JSON config with same basename
        json_path = path.with_suffix('.json')
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print("[ERROR] Cannot load YAML config without pyyaml. Install pyyaml or use JSON config.")
        return {}
    else:
        # Unknown extension, try JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Cannot parse config: {config_path}")
            return {}


def build_arg_parser(description="数据生成脚本"):
    """构建通用命令行参数解析器"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--count', '-n', type=int, default=None, help='生成数量')
    parser.add_argument('--seed', '-s', type=int, default=None, help='随机种子（固定后结果可复现）')
    parser.add_argument('--output', '-o', type=str, default=None, help='输出文件路径')
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件路径')
    return parser


# ============================================================
# 中文姓名生成
# ============================================================

SURNAMES = [
    "王", "李", "张", "刘", "陈", "杨", "黄", "赵", "吴", "周",
    "徐", "孙", "马", "朱", "胡", "郭", "何", "林", "罗", "高",
    "梁", "郑", "谢", "宋", "唐", "韩", "曹", "许", "邓", "冯",
    "萧", "程", "蔡", "彭", "潘", "袁", "于", "董", "余", "叶",
    "蒋", "杜", "苏", "魏", "吕", "田", "丁", "沈", "姜", "范",
    "江", "傅", "钟", "卢", "汪", "戴", "崔", "任", "陆", "廖",
    "姚", "方", "金", "邱", "夏", "谭", "韦", "贾", "邹", "石",
    "熊", "孟", "秦", "阎", "薛", "侯", "雷", "白", "龙", "段",
    "郝", "孔", "邵", "史", "毛", "常", "万", "顾", "赖", "武",
    "康", "贺", "严", "尹", "钱", "施", "牛", "洪", "龚", "欧阳",
    "司马", "上官", "诸葛", "皇甫", "宇文", "慕容",
]

MALE_GIVEN = [
    "伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "明", "超",
    "华", "林", "鹏", "飞", "刚", "平", "辉", "玲", "建国", "志强",
    "文博", "宇轩", "浩然", "子涵", "梓豪", "一鸣", "天宇", "俊杰",
    "思远", "博文", "嘉诚", "睿", "骏", "泽宇", "昊天", "浩宇",
    "瑾瑜", "辰逸", "皓轩", "文昊", "修洁", "黎昕", "远航", "旭尧",
    "英杰", "正豪", "立诚", "立轩", "立辉", "峻熙", "嘉懿", "煜城",
    "铭泽", "奕辰", "逸飞", "子骞", "子默", "子轩", "景行", "鸿飞",
]

FEMALE_GIVEN = [
    "芳", "敏", "静", "丽", "婷", "雪", "玲", "萍", "红", "霞",
    "秀英", "秀兰", "桂英", "淑芬", "文娟", "晓红", "雅文", "美玲",
    "雨桐", "梓涵", "诗涵", "欣怡", "思雨", "语嫣", "若溪", "紫萱",
    "梦琪", "晓雪", "心怡", "雪婷", "悦然", "清雅", "曼琳", "慧妍",
    "乐瑶", "佳琪", "一诺", "艺涵", "芷若", "妙彤", "初夏", "凌薇",
    "云熙", "月婵", "雪莹", "灵犀", "梦瑶", "怡然", "浅汐", "安澜",
]


def generate_name(gender=None):
    """生成中文姓名，gender=None 随机性别，gender='male'/'female' 指定性别"""
    if gender is None:
        gender = random.choice(['male', 'female'])
    surname = random.choice(SURNAMES)
    if gender == 'male':
        given = random.choice(MALE_GIVEN)
    else:
        given = random.choice(FEMALE_GIVEN)
    return surname + given


# ============================================================
# 手机号生成
# ============================================================

MOBILE_PREFIXES = [
    "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
    "150", "151", "152", "153", "155", "156", "157", "158", "159",
    "170", "176", "177", "178",
    "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
    "191", "193", "195", "196", "197", "198", "199",
]


def generate_phone():
    """生成中国手机号"""
    prefix = random.choice(MOBILE_PREFIXES)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


# ============================================================
# 邮箱生成
# ============================================================

EMAIL_DOMAINS = [
    "@qq.com", "@163.com", "@126.com", "@sina.com", "@gmail.com",
    "@outlook.com", "@hotmail.com", "@139.com", "@189.cn", "@foxmail.com",
]


def generate_email(name=""):
    """根据中文姓名生成一个合理的邮箱地址（拼音首字母 + 数字）"""
    if name:
        # 简单模拟：用姓名的拼音首字母组合（这里用随机字母近似）
        initials = ''.join([chr(ord(c) + random.randint(0, 2)) if '一' <= c <= '鿿' else c for c in name])
        # 对中文名使用随机字母数字组合模拟拼音
        prefix = 'py_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(5, 8)))
    else:
        prefix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(6, 10)))

    if random.random() < 0.4:
        prefix += str(random.randint(0, 9999))

    return prefix + random.choice(EMAIL_DOMAINS)


# ============================================================
# 收货地址生成（省市区三级联动 + 邮政编码）
# ============================================================

CITY_DATA = {
    "北京市": {
        "districts": ["东城区", "西城区", "朝阳区", "海淀区", "丰台区", "石景山区", "通州区", "大兴区", "昌平区", "顺义区"],
        "postal": "10####",
        "street_templates": ["{road}路{num}号", "{district}街道{num}号院{block}号楼", "{community}小区{num}号楼{unit}单元"],
    },
    "上海市": {
        "districts": ["浦东新区", "徐汇区", "长宁区", "静安区", "黄浦区", "杨浦区", "闵行区", "宝山区", "嘉定区", "松江区"],
        "postal": "20####",
        "street_templates": ["{road}路{num}号", "{district}街道{num}弄{block}号", "{community}小区{num}号楼"],
    },
    "广东省": {
        "cities": {
            "广州市": {
                "districts": ["天河区", "越秀区", "海珠区", "白云区", "番禺区", "黄埔区", "荔湾区", "花都区"],
                "postal": "510###",
            },
            "深圳市": {
                "districts": ["南山区", "福田区", "罗湖区", "宝安区", "龙岗区", "龙华区", "光明区", "盐田区"],
                "postal": "518###",
            },
            "东莞市": {
                "districts": ["东城街道", "南城街道", "万江街道", "莞城街道", "虎门镇", "长安镇", "厚街镇"],
                "postal": "523###",
            },
            "佛山市": {
                "districts": ["禅城区", "南海区", "顺德区", "三水区", "高明区"],
                "postal": "528###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}花园{num}栋{unit}号", "{district}{road}街{num}号"],
    },
    "浙江省": {
        "cities": {
            "杭州市": {
                "districts": ["西湖区", "拱墅区", "上城区", "滨江区", "余杭区", "萧山区", "临平区", "钱塘区"],
                "postal": "310###",
            },
            "宁波市": {
                "districts": ["海曙区", "鄞州区", "江北区", "北仑区", "镇海区", "奉化区"],
                "postal": "315###",
            },
            "温州市": {
                "districts": ["鹿城区", "龙湾区", "瓯海区", "洞头区"],
                "postal": "325###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}幢{unit}室", "{road}街{num}号{block}楼"],
    },
    "江苏省": {
        "cities": {
            "南京市": {
                "districts": ["玄武区", "秦淮区", "建邺区", "鼓楼区", "栖霞区", "雨花台区", "江宁区", "浦口区"],
                "postal": "210###",
            },
            "苏州市": {
                "districts": ["姑苏区", "虎丘区", "吴中区", "相城区", "吴江区", "工业园区"],
                "postal": "215###",
            },
            "无锡市": {
                "districts": ["梁溪区", "锡山区", "惠山区", "滨湖区", "新吴区"],
                "postal": "214###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}花园{num}栋{unit}室", "{road}大道{num}号"],
    },
    "四川省": {
        "cities": {
            "成都市": {
                "districts": ["锦江区", "青羊区", "金牛区", "武侯区", "成华区", "高新区", "天府新区", "龙泉驿区"],
                "postal": "610###",
            },
            "绵阳市": {
                "districts": ["涪城区", "游仙区", "安州区"],
                "postal": "621###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}栋{unit}号", "{road}街{num}号"],
    },
    "湖北省": {
        "cities": {
            "武汉市": {
                "districts": ["武昌区", "洪山区", "江岸区", "江汉区", "硚口区", "汉阳区", "青山区", "东西湖区", "光谷"],
                "postal": "430###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}栋{unit}室", "{road}大道{num}号"],
    },
    "湖南省": {
        "cities": {
            "长沙市": {
                "districts": ["岳麓区", "芙蓉区", "天心区", "开福区", "雨花区", "望城区"],
                "postal": "410###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}栋{unit}房", "{road}街{num}号"],
    },
    "山东省": {
        "cities": {
            "济南市": {
                "districts": ["历下区", "市中区", "槐荫区", "天桥区", "历城区", "长清区"],
                "postal": "250###",
            },
            "青岛市": {
                "districts": ["市南区", "市北区", "崂山区", "李沧区", "城阳区", "黄岛区"],
                "postal": "266###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}号楼{unit}单元", "{road}大街{num}号"],
    },
    "福建省": {
        "cities": {
            "福州市": {
                "districts": ["鼓楼区", "台江区", "仓山区", "晋安区", "马尾区", "长乐区"],
                "postal": "350###",
            },
            "厦门市": {
                "districts": ["思明区", "湖里区", "集美区", "海沧区", "同安区", "翔安区"],
                "postal": "361###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}栋{unit}室", "{road}街{num}号"],
    },
    "河南省": {
        "cities": {
            "郑州市": {
                "districts": ["金水区", "中原区", "二七区", "管城回族区", "惠济区", "郑东新区"],
                "postal": "450###",
            },
        },
        "street_templates": ["{road}路{num}号", "{community}小区{num}号楼{unit}号", "{road}街{num}号"],
    },
}

ROAD_NAMES = [
    "中山", "人民", "解放", "建设", "和平", "长安", "复兴", "建国", "新华", "朝阳",
    "南京", "北京", "滨河", "花园", "科技", "学府", "文化", "青年", "长江", "黄河",
    "太白", "朱雀", "玄武", "青龙", "凤凰", "龙泉", "翠微", "芙蓉", "丁香", "海棠",
]

COMMUNITY_NAMES = [
    "阳光花园", "世纪城", "碧水湾", "翡翠城", "金色家园", "绿城百合", "万科城",
    "保利花园", "翠湖春晓", "香榭丽舍", "半岛花园", "江南水乡", "紫荆花园",
    "锦绣江南", "华润城", "龙湖春江", "中海国际", "融创壹号", "星河湾", "天鹅湖",
]


def generate_address():
    """生成中国收货地址：省、市、区、详细地址、邮编、收件人姓名和电话"""
    province = random.choice(list(CITY_DATA.keys()))
    prov_data = CITY_DATA[province]

    if province in ("北京市", "上海市"):
        # 直辖市：省=市
        city = province
        district = random.choice(prov_data["districts"])
        postal_pattern = prov_data["postal"]
        templates = prov_data["street_templates"]
    else:
        city = random.choice(list(prov_data["cities"].keys()))
        city_data = prov_data["cities"][city]
        district = random.choice(city_data["districts"])
        postal_pattern = city_data["postal"]
        templates = prov_data.get("street_templates", ["{road}路{num}号"])

    # 生成详细地址
    template = random.choice(templates)
    detail = template.format(
        road=random.choice(ROAD_NAMES),
        num=random.randint(1, 500),
        block=random.randint(1, 30),
        unit=random.randint(1, 5),
        community=random.choice(COMMUNITY_NAMES),
        district=district,
    )

    # 生成邮编
    postal_code = postal_pattern.replace("####", f"{random.randint(0, 9999):04d}")
    postal_code = postal_code.replace("###", f"{random.randint(0, 999):03d}")

    recipient_name = generate_name()
    recipient_phone = generate_phone()

    return {
        "province": province,
        "city": city,
        "district": district,
        "detail": detail,
        "postal_code": postal_code,
        "recipient_name": recipient_name,
        "recipient_phone": recipient_phone,
    }


# ============================================================
# 支付方式
# ============================================================

PAYMENT_METHODS = [
    {"name": "微信支付", "weight": 40},
    {"name": "支付宝", "weight": 35},
    {"name": "银行卡", "weight": 15},
    {"name": "信用卡", "weight": 10},
]


def get_payment_method():
    """按权重随机选择支付方式"""
    methods = [m["name"] for m in PAYMENT_METHODS]
    weights = [m["weight"] for m in PAYMENT_METHODS]
    return random.choices(methods, weights=weights, k=1)[0]


# ============================================================
# 物流公司
# ============================================================

LOGISTICS_COMPANIES = [
    {"name": "顺丰速运", "prefix": "SF", "weight": 25},
    {"name": "京东物流", "prefix": "JD", "weight": 25},
    {"name": "中通快递", "prefix": "ZTO", "weight": 10},
    {"name": "圆通速递", "prefix": "YTO", "weight": 10},
    {"name": "韵达快递", "prefix": "YD", "weight": 7},
    {"name": "申通快递", "prefix": "STO", "weight": 8},
    {"name": "极兔速递", "prefix": "JT", "weight": 5},
    {"name": "中国邮政", "prefix": "EMS", "weight": 5},
    {"name": "德邦快递", "prefix": "DB", "weight": 3},
    {"name": "百世快递", "prefix": "BS", "weight": 2},
]


def get_logistics_company():
    """按权重随机选择物流公司"""
    companies = [c["name"] for c in LOGISTICS_COMPANIES]
    weights = [c["weight"] for c in LOGISTICS_COMPANIES]
    return random.choices(companies, weights=weights, k=1)[0]


def generate_tracking_number(company_name=None):
    """生成运单号"""
    if company_name:
        for c in LOGISTICS_COMPANIES:
            if c["name"] == company_name:
                prefix = c["prefix"]
                break
        else:
            prefix = "EXP"
    else:
        prefix = "EXP"

    digits = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    return f"{prefix}{random.randint(1000, 9999)}{digits}"


# ============================================================
# 订单备注模板
# ============================================================

ORDER_REMARKS = [
    "请尽快发货",
    "易碎品，请注意包装",
    "工作日收货，请勿周末配送",
    "放快递柜即可",
    "请电话联系后再配送",
    "请发顺丰",
    "送礼用，请包装好",
    "颜色请核对后再发货",
    "如有破损请勿签收",
    "需要发票，请随货发出",
    "配送前请电话确认",
    "放门口即可",
    "加急处理",
    "老客户了，给个优惠",
    "生日礼物，请按时送达",
]


# ============================================================
# 通用随机工具函数
# ============================================================

def random_float(min_val, max_val, decimals=2):
    """生成指定范围内的随机浮点数"""
    value = random.uniform(min_val, max_val)
    return round(value, decimals)


def random_int(min_val, max_val):
    """生成指定范围内的随机整数（含两端）"""
    return random.randint(min_val, max_val)


def random_datetime(days_back=90, start=None, end=None):
    """生成随机日期时间，默认近 days_back 天内"""
    if start is None and end is None:
        now = datetime.now()
        start = now - timedelta(days=days_back)
        end = now
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def generate_short_id(prefix="", length=8):
    """生成短 ID"""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    suffix = ''.join(random.choices(chars, k=length))
    return f"{prefix}{suffix}" if prefix else suffix


def generate_order_id():
    """生成订单ID：ORD + 年月日时分秒 + 随机数"""
    now = datetime.now()
    ts = now.strftime("%Y%m%d%H%M%S")
    rand = str(random.randint(100, 999))
    return f"ORD{ts}{rand}"


def generate_product_uuid():
    """生成商品唯一 ID"""
    return str(uuid.uuid4())


def weighted_choice(choices_with_weights):
    """加权随机选择：[(value, weight), ...]"""
    values = [c[0] for c in choices_with_weights]
    weights = [c[1] for c in choices_with_weights]
    return random.choices(values, weights=weights, k=1)[0]


# ============================================================
# 初始化随机种子
# ============================================================

def set_seed(seed):
    """设置随机种子，None 表示不固定"""
    if seed is not None:
        random.seed(seed)
        return True
    return False
