# 配置文件

# 默认图像最长边大小
DEFAULT_LONGEST_SIDE = 1280

# API配置
API_CONFIG = {
    "timeout": 30,
    "max_retries": 3
}

# OCR服务配置
OCR_API_URL = "http://192.168.48.236:8080/layout-parsing"

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
    "log_level": "info"
}