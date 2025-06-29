import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json

def generate_random_string(length: int = 32) -> str:
    """
    生成随机字符串
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_key() -> str:
    """
    生成API密钥
    """
    return f"owl_{generate_random_string(40)}"

def generate_recharge_code(length: int = 16) -> str:
    """
    生成充值码
    """
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # 添加分隔符提高可读性
    return '-'.join([code[i:i+4] for i in range(0, len(code), 4)])

def hash_string(text: str) -> str:
    """
    计算字符串哈希值
    """
    return hashlib.sha256(text.encode()).hexdigest()

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def format_duration(seconds: int) -> str:
    """
    格式化时间长度
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}小时{remaining_minutes}分钟"

def calculate_task_cost(task_type: str, duration_minutes: int, gpu_count: int = 1) -> float:
    """
    计算任务成本
    """
    # 基础费率（每分钟每GPU）
    base_rates = {
        'training': 0.1,      # 训练任务
        'inference': 0.05,    # 推理任务
        'data_processing': 0.03  # 数据处理
    }
    
    rate = base_rates.get(task_type, 0.1)
    total_cost = rate * duration_minutes * gpu_count
    
    return round(total_cost, 2)

def paginate_results(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """
    分页处理
    """
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    paginated_items = items[start_index:end_index]
    
    return {
        'items': paginated_items,
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全的JSON序列化
    """
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default

def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    遮蔽敏感数据
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return visible_part + masked_part

def get_client_ip(request) -> str:
    """
    获取客户端IP地址
    """
    # 检查代理头
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.client.host

def is_valid_json(json_str: str) -> bool:
    """
    检查是否为有效的JSON字符串
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def filter_dict_keys(data: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
    """
    过滤字典键
    """
    return {k: v for k, v in data.items() if k in allowed_keys}

def get_time_range(period: str) -> tuple[datetime, datetime]:
    """
    获取时间范围
    """
    now = datetime.utcnow()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'week':
        start = now - timedelta(days=7)
        end = now
    elif period == 'month':
        start = now - timedelta(days=30)
        end = now
    elif period == 'year':
        start = now - timedelta(days=365)
        end = now
    else:
        # 默认返回最近24小时
        start = now - timedelta(hours=24)
        end = now
    
    return start, end

def calculate_percentage(part: float, total: float) -> float:
    """
    计算百分比
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix