#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kafka 推送模块：生产者连接、消息发送、连接管理

同时支持 kafka-python（纯 Python）和 confluent-kafka（基于 librdkafka，性能更高）
优先使用 confluent-kafka，回退 kafka-python，均未安装时给出提示。
"""

import json
import re
import os
import sys

# ============================================================
# 可选依赖检测：confluent-kafka（优先）> kafka-python（回退）
# ============================================================
_KAFKA_BACKEND = None  # 'confluent' | 'kafka-python' | None
_KAFKA_AVAILABLE = False

# 优先 confluent-kafka（C 库，与企业 Kafka 更兼容）
try:
    from confluent_kafka import Producer as ConfluentProducer
    from confluent_kafka import KafkaException as ConfluentKafkaException
    _KAFKA_BACKEND = 'confluent'
    _KAFKA_AVAILABLE = True
except ImportError:
    pass

# 回退 kafka-python（纯 Python）
if not _KAFKA_AVAILABLE:
    try:
        from kafka import KafkaProducer
        from kafka.errors import KafkaError, NoBrokersAvailable
        _KAFKA_BACKEND = 'kafka-python'
        _KAFKA_AVAILABLE = True
    except ImportError:
        pass

# 输出 URI 正则：kafka://host:port/topic
KAFKA_URI_PATTERN = re.compile(r'^kafka://([^:/]+)(?::(\d+))?/(.+)$')


def parse_output_uri(output_arg):
    """
    解析 --output 参数，返回 (mode, config)
    mode: 'file' 或 'kafka'
    config: file 模式返回 {'path': str}，kafka 模式返回 {'host': str, 'port': int, 'topic': str}
    """
    if not output_arg:
        return ('file', {'path': 'output/products.json'})

    match = KAFKA_URI_PATTERN.match(output_arg)
    if match:
        host = match.group(1)
        port = int(match.group(2)) if match.group(2) else 9092
        topic = match.group(3)
        return ('kafka', {'host': host, 'port': port, 'topic': topic})

    return ('file', {'path': output_arg})


def _create_producer_confluent(bootstrap_servers, timeout=10):
    """使用 confluent-kafka 创建生产者"""
    config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'datagenerate-python',
        'socket.timeout.ms': timeout * 1000,
        'socket.connection.setup.timeout.ms': timeout * 1000,
        'request.timeout.ms': timeout * 1000,
    }
    try:
        producer = ConfluentProducer(config)
        # 快速验证连接：发送 metadata 请求
        metadata = producer.list_topics(timeout=timeout)
        return (producer, None)
    except ConfluentKafkaException as e:
        return (None, f"无法连接到 Kafka Broker: {bootstrap_servers} - {e}")
    except Exception as e:
        return (None, f"Kafka 连接失败: {e}")


def _create_producer_kafka_python(bootstrap_servers, timeout=10):
    """使用 kafka-python 创建生产者"""
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        max_block_ms=timeout * 1000,
        api_version_auto_timeout_ms=timeout * 1000,
        request_timeout_ms=timeout * 1000,
    )
    return (producer, None)


def create_kafka_producer(host, port, timeout=10):
    """
    创建 Kafka 生产者连接（自动选择后端）
    返回 (producer, error_message)
    """
    if not _KAFKA_AVAILABLE:
        return (None, "Kafka 客户端未安装。安装方式: pip install confluent-kafka  (或 pip install kafka-python)")

    bootstrap_servers = f"{host}:{port}"
    print(f"[INFO] Kafka 后端: {_KAFKA_BACKEND}")

    try:
        if _KAFKA_BACKEND == 'confluent':
            return _create_producer_confluent(bootstrap_servers, timeout)
        else:
            return _create_producer_kafka_python(bootstrap_servers, timeout)
    except NoBrokersAvailable as e:
        return (None, f"无法连接到 Kafka Broker: {bootstrap_servers} - {e}")
    except Exception as e:
        return (None, f"Kafka 连接失败: {e}")


def send_to_kafka(producer, topic, key, value, max_retries=3):
    """
    发送一条消息到 Kafka topic
    返回 (success, error_message)
    """
    # 序列化
    value_bytes = json.dumps(value, ensure_ascii=False).encode('utf-8')
    key_bytes = key.encode('utf-8') if key else None

    for attempt in range(max_retries):
        try:
            if _KAFKA_BACKEND == 'confluent':
                producer.produce(topic, key=key_bytes, value=value_bytes)
                producer.flush(timeout=5)
                return (True, None)
            else:
                future = producer.send(topic, key=key, value=value)
                future.get(timeout=5)
                return (True, None)
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            else:
                return (False, str(e))

    return (False, "max_retries exceeded")


class KafkaOutputManager:
    """管理 Kafka 输出：连接、发送、关闭、进度追踪"""

    def __init__(self, host, port, topic, file_backup_path=None):
        self.host = host
        self.port = port
        self.topic = topic
        self.file_backup_path = file_backup_path
        self.producer = None
        self.error_count = 0
        self.success_count = 0
        self.backup_data = []  # 本地备份缓冲
        self._connected = False

    def connect(self):
        """建立 Kafka 连接"""
        self.producer, error = create_kafka_producer(self.host, self.port)
        if error:
            print(f"[ERROR] {error}")
            return False
        self._connected = True
        print(f"[INFO] Kafka 已连接: {self.host}:{self.port}, topic={self.topic}")
        return True

    def send(self, key, record):
        """发送单条记录 + 本地备份"""
        # 本地备份
        if self.file_backup_path:
            self.backup_data.append(record)

        if not self._connected:
            return True

        success, error = send_to_kafka(self.producer, self.topic, key, record)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if self.error_count <= 10:
                print(f"[WARN] Kafka 发送失败 (key={key}): {error}")

        return success

    def flush(self):
        """刷新 Kafka 缓冲 + 写入本地备份文件"""
        if self._connected and self.producer:
            try:
                if _KAFKA_BACKEND == 'confluent':
                    self.producer.flush(timeout=30)
                else:
                    self.producer.flush(timeout=30)
            except Exception as e:
                print(f"[WARN] Kafka flush 失败: {e}")

        # 写入本地备份文件
        if self.file_backup_path and self.backup_data:
            os.makedirs(os.path.dirname(self.file_backup_path) or '.', exist_ok=True)
            with open(self.file_backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 本地备份文件: {self.file_backup_path} ({len(self.backup_data)} 条)")

    def close(self):
        """关闭连接"""
        if self._connected and self.producer:
            try:
                if hasattr(self.producer, 'close'):
                    self.producer.close()
                print(f"[INFO] Kafka 连接已关闭")
            except Exception:
                pass

        self._connected = False

    def get_stats(self):
        """获取统计信息"""
        return {
            'connected': self._connected,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'backup_count': len(self.backup_data),
            'backend': _KAFKA_BACKEND,
        }
