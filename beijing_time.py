#!/usr/bin/env python3
"""
北京时间（UTC+8）统一处理模块
确保整个系统使用一致的时区标准
"""

from datetime import datetime, timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def get_beijing_timestamp() -> str:
    """获取北京时间戳字符串（用于日志）"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S CST')

def get_beijing_date_str() -> str:
    """获取北京日期字符串（YYYY-MM-DD）"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')

def to_beijing_time(dt: datetime) -> datetime:
    """将任意datetime转换为北京时间"""
    if dt.tzinfo is None:
        # 假设为UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING_TZ)

def get_today_range_beijing() -> tuple:
    """获取北京时间的今日范围（开始时间，结束时间）"""
    bj_now = datetime.now(BEIJING_TZ)
    today_start = datetime(bj_now.year, bj_now.month, bj_now.day, 0, 0, 0, tzinfo=BEIJING_TZ)
    today_end = datetime(bj_now.year, bj_now.month, bj_now.day, 23, 59, 59, tzinfo=BEIJING_TZ)
    return today_start, today_end

def format_beijing_time(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化北京时间"""
    beijing_dt = to_beijing_time(dt)
    return beijing_dt.strftime(format_str)

__all__ = [
    'BEIJING_TZ',
    'get_beijing_time',
    'get_beijing_timestamp',
    'get_beijing_date_str',
    'to_beijing_time',
    'get_today_range_beijing',
    'format_beijing_time',
]
