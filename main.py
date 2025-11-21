#!/usr/bin/env python3
"""
PDF处理服务入口
支持命令行模式和FastAPI服务器模式
"""

import argparse
import sys
from pathlib import Path
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def run_cli():
    """运行命令行模式"""
    from utils.utils import process_pdf_file
    
    parser = argparse.ArgumentParser(description='处理PDF文件并进行布局解析')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('--api-url', default='http://192.168.48.236:8080/layout-parsing', 
                       help='布局解析API URL')
    parser.add_argument('--output-dir', default='output', help='输出目录')
    parser.add_argument('--longest-side', type=int, default=1280, 
                       help='图像最长边像素大小')
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"错误: PDF文件不存在: {args.pdf_path}")
        sys.exit(1)
    
    print(f"开始处理PDF文件: {pdf_path.name}")
    print(f"API地址: {args.api_url}")
    print(f"输出目录: {args.output_dir}")
    print(f"图像最大边长: {args.longest_side}px")
    print("-" * 50)
    
    try:
        # 处理PDF文件
        result = process_pdf_file(
            pdf_path=str(pdf_path),
            api_url=args.api_url,
            output_dir=args.output_dir,
            longest_side=args.longest_side
        )
        
        print("\n处理完成!")
        print(f"总页数: {result['total_pages']}")
        print(f"成功处理页数: {result['processed_pages']}")
        print(f"输出文件保存在: {args.output_dir}")
        
        if result['processed_pages'] < result['total_pages']:
            print(f"警告: 有 {result['total_pages'] - result['processed_pages']} 页处理失败")
            
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_server():
    """运行FastAPI服务器"""
    print("启动PDF处理服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print("-" * 50)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


def main():
    parser = argparse.ArgumentParser(description='PDF处理服务')
    parser.add_argument('--server', action='store_true', help='启动FastAPI服务器')
    parser.add_argument('--cli', action='store_true', help='运行命令行模式')
    
    args = parser.parse_args()
    
    if args.server:
        run_server()
    elif args.cli:
        run_cli()
    else:
        # 默认启动服务器
        run_server()


if __name__ == "__main__":
    main()