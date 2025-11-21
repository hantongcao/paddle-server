"""
FastAPI应用 - PDF处理服务
提供健康检查接口和PDF处理接口
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import json
import tempfile
import os
import asyncio
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.utils import process_pdf_file
from config.config import OCR_API_URL, DEFAULT_LONGEST_SIDE

# 创建FastAPI应用
app = FastAPI(
    title="PDF处理服务",
    description="提供PDF文件处理和布局解析功能的API服务",
    version="1.0.0"
)

# 信号量控制 - 限制PDF处理为单并发
processing_semaphore = asyncio.Semaphore(1)

@app.get("/health")
async def health_check():
    """
    健康检查接口
    返回服务状态信息
    """
    return {
        "status": "healthy",
        "service": "pdf-processing-service",
        "version": "1.0.0"
    }

@app.post("/process-pdf")
async def process_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    api_url: str = "http://192.168.48.236:8080/layout-parsing",
    longest_side: int = 1280
):
    """
    处理PDF文件接口
    
    接收PDF文件，按页拆分为图像，调整大小，并进行布局解析
    
    Args:
        file: 上传的PDF文件
        api_url: 布局解析API地址
        longest_side: 图像最长边像素大小
        
    Returns:
        JSON格式的解析结果，包含每页的markdown内容
    """
    # 检查并发控制 - 如果信号量被占用，返回429状态码
    if not processing_semaphore.locked():
        try:
            # 尝试获取信号量，设置超时时间为0
            await asyncio.wait_for(processing_semaphore.acquire(), timeout=0)
        except asyncio.TimeoutError:
            # 信号量已被占用，返回429 Too Many Requests
            raise HTTPException(
                status_code=429,
                detail="系统繁忙，请稍后再试。当前仅支持单并发处理。"
            )
    else:
        # 信号量已被占用，返回429 Too Many Requests
        raise HTTPException(
            status_code=429,
            detail="系统繁忙，请稍后再试。当前仅支持单并发处理。"
        )
    
    try:
        # 检查文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="仅支持PDF文件"
            )
        
        # 读取上传的文件内容
        file_content = await file.read()
        
        # 使用临时文件处理
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # 处理PDF文件
            result_json = process_pdf_file(
                pdf_input=temp_file_path,
                api_url=api_url,
                longest_side=longest_side
            )
            
            # 解析JSON结果
            result_data = json.loads(result_json)
            
            return JSONResponse(
                content={
                    "success": True,
                    "filename": file.filename,
                    "total_pages": len(result_data),
                    "results": result_data
                },
                status_code=200
            )
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"处理PDF文件时发生错误: {str(e)}"
        )
    finally:
        # 释放信号量
        processing_semaphore.release()

@app.get("/")
async def root():
    """
    根路径接口
    返回API基本信息
    """
    return {
        "message": "PDF处理服务API",
        "endpoints": {
            "health_check": "/health",
            "process_pdf": "/process-pdf",
            "docs": "/docs"
        }
    }