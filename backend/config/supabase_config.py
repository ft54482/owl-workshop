# -*- coding: utf-8 -*-
"""
🦉 猫头鹰工厂 - Supabase配置管理
统一管理Supabase连接和配置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from supabase import create_client, Client
from loguru import logger

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "猫头鹰工厂"
    app_version: str = "0.10.0"
    debug: bool = True
    host: str = "localhost"
    port: int = 8000
    
    # Supabase配置
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class SupabaseManager:
    """Supabase连接管理器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """获取普通客户端"""
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_anon_key
            )
        return self._client
    
    @property
    def admin_client(self) -> Client:
        """获取管理员客户端"""
        if self._admin_client is None:
            self._admin_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key
            )
        return self._admin_client
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = self.client.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase连接测试失败: {e}")
            return False

# 创建全局配置实例
settings = Settings()
supabase_manager = SupabaseManager(settings)

# 导出
__all__ = ["settings", "supabase_manager", "Settings", "SupabaseManager"]