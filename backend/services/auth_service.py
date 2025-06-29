import logging
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models.database_models import User, UserCreate
from ..config.supabase_config import get_supabase_manager, AppConfig

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """
    认证服务类
    """
    
    def __init__(self):
        self.supabase = get_supabase_manager().get_client()
        self.config = AppConfig()
    
    def hash_password(self, password: str) -> str:
        """
        加密密码
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.config.jwt_secret_key, 
            algorithm=self.config.jwt_algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        验证令牌
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.jwt_secret_key, 
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.debug(f"令牌验证失败: {str(e)}")
            return None
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户
        """
        try:
            # 检查邮箱是否已存在
            existing_user = self.supabase.table('users').select('*').eq('email', user_data.email).execute()
            if existing_user.data:
                raise Exception("邮箱已被注册")
            
            # 检查用户名是否已存在
            existing_username = self.supabase.table('users').select('*').eq('username', user_data.username).execute()
            if existing_username.data:
                raise Exception("用户名已被使用")
            
            # 加密密码
            hashed_password = self.hash_password(user_data.password)
            
            # 准备用户数据
            user_dict = {
                'email': user_data.email,
                'username': user_data.username,
                'full_name': user_data.full_name,
                'password_hash': hashed_password,
                'role': 'user',  # 默认角色
                'is_active': True,
                'balance': 0.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # 插入用户
            result = self.supabase.table('users').insert(user_dict).execute()
            
            if not result.data:
                raise Exception("创建用户失败")
            
            user = User(**result.data[0])
            logger.info(f"用户创建成功: {user.email}")
            
            return user
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        """
        try:
            # 查找用户
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            
            # 验证密码
            if not self.verify_password(password, user_data['password_hash']):
                return None
            
            user = User(**user_data)
            logger.info(f"用户认证成功: {user.email}")
            
            return user
            
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据ID获取用户
        """
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            
            if not result.data:
                return None
            
            return User(**result.data[0])
            
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        """
        try:
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                return None
            
            return User(**result.data[0])
            
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None
    
    async def update_user_login_time(self, user_id: str):
        """
        更新用户最后登录时间
        """
        try:
            self.supabase.table('users').update({
                'last_login': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
        except Exception as e:
            logger.error(f"更新用户登录时间失败: {str(e)}")
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        修改密码
        """
        try:
            # 获取用户当前密码
            result = self.supabase.table('users').select('password_hash').eq('id', user_id).execute()
            
            if not result.data:
                return False
            
            current_password_hash = result.data[0]['password_hash']
            
            # 验证旧密码
            if not self.verify_password(old_password, current_password_hash):
                return False
            
            # 加密新密码
            new_password_hash = self.hash_password(new_password)
            
            # 更新密码
            self.supabase.table('users').update({
                'password_hash': new_password_hash,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            logger.info(f"用户密码修改成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"修改密码失败: {str(e)}")
            return False
    
    async def reset_password(self, email: str) -> bool:
        """
        重置密码（发送重置邮件）
        """
        try:
            # 检查用户是否存在
            user = await self.get_user_by_email(email)
            if not user:
                return False
            
            # 生成重置令牌
            reset_token = self.create_access_token(
                data={"sub": user.id, "type": "password_reset"},
                expires_delta=timedelta(hours=1)  # 1小时有效期
            )
            
            # 这里应该发送重置邮件
            # 目前只记录日志
            logger.info(f"密码重置令牌生成: {user.email}, token: {reset_token}")
            
            return True
            
        except Exception as e:
            logger.error(f"重置密码失败: {str(e)}")
            return False
    
    async def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """
        确认密码重置
        """
        try:
            # 验证令牌
            payload = self.verify_token(token)
            if not payload or payload.get('type') != 'password_reset':
                return False
            
            user_id = payload.get('sub')
            if not user_id:
                return False
            
            # 更新密码
            new_password_hash = self.hash_password(new_password)
            
            self.supabase.table('users').update({
                'password_hash': new_password_hash,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            logger.info(f"密码重置成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"确认密码重置失败: {str(e)}")
            return False
    
    def check_user_permission(self, user: User, required_role: str) -> bool:
        """
        检查用户权限
        """
        role_hierarchy = {
            'user': 0,
            'admin': 1,
            'super_admin': 2
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level