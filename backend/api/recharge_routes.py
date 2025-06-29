from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime
import uuid
import secrets
import string

from ..models.database_models import (
    User, APIResponse, PaginatedResponse, RechargeCode, RechargeRecord
)
from ..middleware.supabase_auth import get_current_user, require_admin
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recharge", tags=["充值管理"])

class CreateRechargeCodeRequest(BaseModel):
    amount: float
    quantity: int = 1
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class UseRechargeCodeRequest(BaseModel):
    code: str

def generate_recharge_code(length: int = 16) -> str:
    """
    生成充值码
    """
    characters = string.ascii_uppercase + string.digits
    # 排除容易混淆的字符
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(secrets.choice(characters) for _ in range(length))

@router.post("/codes", response_model=APIResponse[List[RechargeCode]])
async def create_recharge_codes(request: CreateRechargeCodeRequest, current_user: User = Depends(require_admin)):
    """
    创建充值码（仅管理员）
    """
    try:
        if request.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="充值金额必须大于0"
            )
        
        if request.quantity <= 0 or request.quantity > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="充值码数量必须在1-100之间"
            )
        
        supabase = get_supabase_manager().get_client()
        created_codes = []
        
        for _ in range(request.quantity):
            # 生成唯一的充值码
            while True:
                code = generate_recharge_code()
                # 检查充值码是否已存在
                existing_code = supabase.table('recharge_codes').select('id').eq('code', code).execute()
                if not existing_code.data:
                    break
            
            # 创建充值码数据
            code_data = {
                'code': code,
                'amount': request.amount,
                'description': request.description,
                'expires_at': request.expires_at.isoformat() if request.expires_at else None,
                'created_by': current_user.id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('recharge_codes').insert(code_data).execute()
            
            if result.data:
                created_codes.append(RechargeCode(**result.data[0]))
        
        logger.info(f"充值码创建成功: {len(created_codes)}个, 金额: {request.amount} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message=f"成功创建{len(created_codes)}个充值码",
            data=created_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建充值码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建充值码失败"
        )

@router.get("/codes", response_model=PaginatedResponse[RechargeCode])
async def get_recharge_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_admin)
):
    """
    获取充值码列表（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 构建查询
        query = supabase.table('recharge_codes').select('*')
        
        # 添加状态过滤
        if status_filter:
            if status_filter == 'unused':
                query = query.is_('used_at', 'null')
            elif status_filter == 'used':
                query = query.not_.is_('used_at', 'null')
            elif status_filter == 'expired':
                query = query.lt('expires_at', datetime.utcnow().isoformat())
        
        # 获取总数
        count_query = supabase.table('recharge_codes').select('id', count='exact')
        if status_filter:
            if status_filter == 'unused':
                count_query = count_query.is_('used_at', 'null')
            elif status_filter == 'used':
                count_query = count_query.not_.is_('used_at', 'null')
            elif status_filter == 'expired':
                count_query = count_query.lt('expires_at', datetime.utcnow().isoformat())
        
        count_result = count_query.execute()
        total = count_result.count
        
        # 分页查询
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
        
        codes = [RechargeCode(**code_data) for code_data in result.data]
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=codes,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取充值码列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取充值码列表失败"
        )

@router.post("/use", response_model=APIResponse)
async def use_recharge_code(request: UseRechargeCodeRequest, current_user: User = Depends(get_current_user)):
    """
    使用充值码
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 查找充值码
        code_result = supabase.table('recharge_codes').select('*').eq('code', request.code).execute()
        
        if not code_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="充值码不存在"
            )
        
        code_data = code_result.data[0]
        
        # 检查充值码是否已使用
        if code_data['used_at']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="充值码已被使用"
            )
        
        # 检查充值码是否过期
        if code_data['expires_at']:
            expires_at = datetime.fromisoformat(code_data['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="充值码已过期"
                )
        
        # 开始事务处理
        # 1. 标记充值码为已使用
        supabase.table('recharge_codes').update({
            'used_at': datetime.utcnow().isoformat(),
            'used_by': current_user.id
        }).eq('id', code_data['id']).execute()
        
        # 2. 更新用户余额
        current_balance = current_user.balance or 0.0
        new_balance = current_balance + code_data['amount']
        
        supabase.table('users').update({
            'balance': new_balance,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', current_user.id).execute()
        
        # 3. 创建充值记录
        record_data = {
            'user_id': current_user.id,
            'amount': code_data['amount'],
            'type': 'recharge_code',
            'description': f"使用充值码: {request.code}",
            'recharge_code_id': code_data['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('recharge_records').insert(record_data).execute()
        
        logger.info(f"充值码使用成功: {request.code}, 金额: {code_data['amount']}, 用户: {current_user.email}")
        
        return APIResponse(
            success=True,
            message=f"充值成功，获得 {code_data['amount']} 元",
            data={
                'amount': code_data['amount'],
                'new_balance': new_balance
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"使用充值码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="使用充值码失败"
        )

@router.get("/records", response_model=PaginatedResponse[RechargeRecord])
async def get_recharge_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    获取充值记录
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 构建查询
        query = supabase.table('recharge_records').select('*').eq('user_id', current_user.id)
        
        # 获取总数
        count_result = supabase.table('recharge_records').select('id', count='exact').eq('user_id', current_user.id).execute()
        total = count_result.count
        
        # 分页查询
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
        
        records = [RechargeRecord(**record_data) for record_data in result.data]
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=records,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取充值记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取充值记录失败"
        )

@router.get("/balance", response_model=APIResponse)
async def get_user_balance(current_user: User = Depends(get_current_user)):
    """
    获取用户余额
    """
    try:
        # 获取最新的用户余额
        supabase = get_supabase_manager().get_client()
        user_result = supabase.table('users').select('balance').eq('id', current_user.id).execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        balance = user_result.data[0]['balance'] or 0.0
        
        return APIResponse(
            success=True,
            message="获取余额成功",
            data={'balance': balance}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户余额失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户余额失败"
        )

@router.delete("/codes/{code_id}", response_model=APIResponse)
async def delete_recharge_code(code_id: str, current_user: User = Depends(require_admin)):
    """
    删除充值码（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查充值码是否存在
        code_result = supabase.table('recharge_codes').select('*').eq('id', code_id).execute()
        
        if not code_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="充值码不存在"
            )
        
        code_data = code_result.data[0]
        
        # 检查充值码是否已被使用
        if code_data['used_at']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已使用的充值码无法删除"
            )
        
        # 删除充值码
        supabase.table('recharge_codes').delete().eq('id', code_id).execute()
        
        logger.info(f"充值码删除成功: {code_data['code']} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="充值码删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除充值码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除充值码失败"
        )