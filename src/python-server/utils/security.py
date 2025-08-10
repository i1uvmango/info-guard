"""
보안 관련 유틸리티 함수들
API 키와 민감한 정보를 로그에서 마스킹하는 기능 제공
"""

import re
import logging
from typing import Any, Dict, List, Union
from functools import wraps


class SensitiveDataFilter(logging.Filter):
    """민감한 데이터를 로그에서 마스킹하는 필터"""
    
    def __init__(self):
        super().__init__()
        # API 키 패턴 (YouTube, Google, OpenAI 등)
        self.api_key_patterns = [
            r'AIza[0-9A-Za-z_-]{35}',  # YouTube API
            r'sk-[0-9a-zA-Z]{48}',      # OpenAI API
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',  # UUID
            r'[0-9]{10,}',              # 긴 숫자 (API 키일 가능성)
        ]
        
        # 민감한 환경 변수명
        self.sensitive_env_vars = [
            'API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'AUTH',
            'YOUTUBE_API_KEY', 'OPENAI_API_KEY', 'GOOGLE_API_KEY',
            'DATABASE_URL', 'REDIS_URL', 'MONGODB_URI'
        ]
        
        # 민감한 키워드
        self.sensitive_keywords = [
            'password', 'secret', 'token', 'key', 'auth', 'credential',
            'api_key', 'private_key', 'access_token', 'refresh_token'
        ]
    
    def filter(self, record):
        """로그 레코드를 필터링하여 민감한 정보를 마스킹"""
        if hasattr(record, 'msg'):
            record.msg = self.mask_sensitive_data(str(record.msg))
        
        if hasattr(record, 'args'):
            record.args = tuple(self.mask_sensitive_data(str(arg)) for arg in record.args)
        
        return True
    
    def mask_sensitive_data(self, text: str) -> str:
        """텍스트에서 민감한 정보를 마스킹"""
        if not isinstance(text, str):
            return text
        
        # API 키 패턴 마스킹
        for pattern in self.api_key_patterns:
            text = re.sub(pattern, '[API_KEY_MASKED]', text)
        
        # 환경 변수 값 마스킹
        for env_var in self.sensitive_env_vars:
            # YOUTUBE_API_KEY=value 형태 마스킹
            text = re.sub(
                rf'{env_var}=([^\s\n\r]+)',
                f'{env_var}=[MASKED]',
                text,
                flags=re.IGNORECASE
            )
        
        # 키워드 기반 마스킹
        for keyword in self.sensitive_keywords:
            # key: value 형태 마스킹
            text = re.sub(
                rf'({keyword}["\s]*:["\s]*)([^\s\n\r,}}]+)',
                r'\1[MASKED]',
                text,
                flags=re.IGNORECASE
            )
        
        return text


def mask_api_key(api_key: str) -> str:
    """API 키를 마스킹된 형태로 반환"""
    if not api_key or len(api_key) < 8:
        return '[INVALID_KEY]'
    
    # 앞 4글자와 뒤 4글자만 보여주고 나머지는 마스킹
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def mask_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """딕셔너리에서 민감한 정보를 마스킹"""
    masked_data = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            masked_data[key] = mask_sensitive_dict(value)
        elif isinstance(value, list):
            masked_data[key] = [mask_sensitive_dict(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(key, str) and any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token', 'auth']):
            if isinstance(value, str) and len(value) > 8:
                masked_data[key] = mask_api_key(value)
            else:
                masked_data[key] = '[MASKED]'
        else:
            masked_data[key] = value
    
    return masked_data


def secure_logging(func):
    """함수의 로깅을 보안적으로 만드는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 함수 실행 전 로그
        logger = logging.getLogger(func.__module__)
        logger.info(f"함수 실행: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"함수 완료: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"함수 오류: {func.__name__} - {str(e)}")
            raise
    
    return wrapper


def setup_secure_logging():
    """보안 로깅 설정"""
    # 루트 로거에 필터 추가
    root_logger = logging.getLogger()
    
    # 기존 핸들러들에 필터 추가
    for handler in root_logger.handlers:
        if not any(isinstance(filter, SensitiveDataFilter) for filter in handler.filters):
            handler.addFilter(SensitiveDataFilter())
    
    # 새로운 핸들러가 추가될 때도 자동으로 필터 적용
    original_addHandler = root_logger.addHandler
    
    def secure_add_handler(handler):
        if not any(isinstance(filter, SensitiveDataFilter) for filter in handler.filters):
            handler.addFilter(SensitiveDataFilter())
        return original_addHandler(handler)
    
    root_logger.addHandler = secure_add_handler


# 로깅 설정 시 자동으로 보안 필터 적용
setup_secure_logging()
