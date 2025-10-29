"""
Configuração de Produção - ARQV30 Enhanced v3.0
Configurações otimizadas para ambiente de produção
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Configuração para ambiente de produção"""
    
    # Configurações básicas do Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'arqv30-enhanced-ultra-secure-key-2024')
    
    # Configurações de servidor
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    THREADED = True
    USE_RELOADER = False
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configurações de CORS para produção
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Configurações de cache
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    SEARCH_CACHE_ENABLED = os.getenv('SEARCH_CACHE_ENABLED', 'true').lower() == 'true'
    SEARCH_CACHE_TTL = int(os.getenv('SEARCH_CACHE_TTL', '3600'))
    
    # Configurações de rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = "100 per hour"
    RATE_LIMIT_STORAGE_URL = "memory://"
    
    # Configurações de compressão
    GZIP_ENABLED = os.getenv('GZIP_ENABLED', 'true').lower() == 'true'
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'text/javascript',
        'application/json', 'application/javascript', 'application/xml'
    ]
    
    # Configurações de timeout
    REQUEST_TIMEOUT = 300  # 5 minutos
    API_TIMEOUT = 60  # 1 minuto
    DOWNLOAD_TIMEOUT = 120  # 2 minutos
    
    # Configurações de recursos
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    MAX_WORKERS = os.cpu_count() or 4
    
    # Configurações de monitoramento
    HEALTH_CHECK_ENABLED = True
    METRICS_ENABLED = True
    PERFORMANCE_MONITORING = True
    
    # Configurações específicas do ARQV30
    REAL_DATA_ONLY = True
    VIRAL_CONTENT_CAPTURE = True
    AI_ACTIVE_SEARCH = True
    API_ROTATION = True
    SCREENSHOT_CAPTURE = True
    
    @classmethod
    def validate_config(cls):
        """Valida configurações críticas para produção"""
        errors = []
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'arqv30-enhanced-ultra-secure-key-2024':
            errors.append("SECRET_KEY deve ser definida com valor único em produção")
        
        if cls.DEBUG:
            errors.append("DEBUG deve ser False em produção")
        
        if cls.TESTING:
            errors.append("TESTING deve ser False em produção")
        
        if '*' in cls.CORS_ORIGINS and len(cls.CORS_ORIGINS) == 1:
            errors.append("CORS_ORIGINS deve ser restritivo em produção (não usar '*')")
        
        if errors:
            raise ValueError(f"Erros de configuração de produção: {'; '.join(errors)}")
        
        return True

class DevelopmentConfig:
    """Configuração para ambiente de desenvolvimento"""
    
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'dev-key-not-secure'
    
    HOST = '127.0.0.1'
    PORT = 5000
    THREADED = True
    USE_RELOADER = True
    
    # Configurações mais permissivas para desenvolvimento
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['*']
    
    LOG_LEVEL = 'DEBUG'
    CACHE_ENABLED = False
    RATE_LIMIT_ENABLED = False

def get_config():
    """Retorna configuração baseada no ambiente"""
    env = os.getenv('FLASK_ENV', 'production')
    
    if env == 'development':
        return DevelopmentConfig()
    else:
        config = ProductionConfig()
        config.validate_config()
        return config