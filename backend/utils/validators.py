import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError

def validate_email_format(email: str) -> bool:
    """
    验证邮箱格式
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    返回: (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, "密码长度至少8位"
    
    if len(password) > 128:
        return False, "密码长度不能超过128位"
    
    # 检查是否包含数字
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    
    # 检查是否包含字母
    if not re.search(r'[a-zA-Z]', password):
        return False, "密码必须包含至少一个字母"
    
    # 检查是否包含特殊字符
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"
    
    return True, None

def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    验证用户名
    """
    if len(username) < 3:
        return False, "用户名长度至少3位"
    
    if len(username) > 50:
        return False, "用户名长度不能超过50位"
    
    # 只允许字母、数字、下划线和连字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "用户名只能包含字母、数字、下划线和连字符"
    
    # 不能以数字开头
    if username[0].isdigit():
        return False, "用户名不能以数字开头"
    
    return True, None

def validate_task_title(title: str) -> tuple[bool, Optional[str]]:
    """
    验证任务标题
    """
    if not title or not title.strip():
        return False, "任务标题不能为空"
    
    if len(title) > 200:
        return False, "任务标题长度不能超过200字符"
    
    return True, None

def validate_gpu_server_config(config: dict) -> tuple[bool, Optional[str]]:
    """
    验证GPU服务器配置
    """
    required_fields = ['host', 'port', 'username']
    
    for field in required_fields:
        if field not in config:
            return False, f"缺少必需字段: {field}"
    
    # 验证主机地址
    host = config['host']
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        return False, "主机地址格式无效"
    
    # 验证端口
    port = config['port']
    if not isinstance(port, int) or port < 1 or port > 65535:
        return False, "端口号必须在1-65535之间"
    
    return True, None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    清理输入文本
    """
    if not text:
        return ""
    
    # 移除前后空白
    text = text.strip()
    
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除潜在的危险字符
    text = re.sub(r'[<>"\']', '', text)
    
    return text