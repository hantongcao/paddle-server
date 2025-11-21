#!/usr/bin/env python3
"""
测试process-pdf接口的脚本
用于验证PDF处理服务的文件上传和处理功能
"""

import requests
import json
import sys
import os
from datetime import datetime

def test_process_pdf_endpoint(pdf_file_path):
    """测试process-pdf接口"""
    
    # 服务地址
    base_url = "http://localhost:8000"
    process_url = f"{base_url}/process-pdf"
    
    print("=" * 70)
    print("📄 Process-PDF接口测试")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {process_url}")
    print(f"PDF文件: {pdf_file_path}")
    print(f"文件大小: {os.path.getsize(pdf_file_path)} bytes")
    print("-" * 70)
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file_path):
        print(f"❌ PDF文件不存在: {pdf_file_path}")
        return False
    
    try:
        # 准备请求参数
        files = {
            'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf')
        }
        
        data = {
            'api_url': 'http://192.168.48.236:8080/layout-parsing',
            'longest_side': '1280'
        }
        
        # 发送POST请求
        response = requests.post(process_url, files=files, data=data, timeout=30)
        
        # 打印响应信息
        print(f"✅ 请求成功!")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response.elapsed.total_seconds():.3f}秒")
        
        # 检查状态码
        if response.status_code == 200:
            print("✅ 状态码: 200 (OK)")
        else:
            print(f"❌ 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        # 解析JSON响应
        try:
            data = response.json()
            print("✅ JSON解析成功")
            
            # 打印响应数据摘要
            print(f"\n📋 响应摘要:")
            print(f"成功: {data.get('success', False)}")
            print(f"文件名: {data.get('filename', 'N/A')}")
            print(f"总页数: {data.get('total_pages', 0)}")
            
            if 'results' in data and data['results']:
                print(f"解析结果数: {len(data['results'])}")
                
                # 显示第一页的结果摘要
                first_result = data['results'][0]
                print(f"\n📄 第一页结果摘要:")
                print(f"页码: {first_result.get('page', 'N/A')}")
                print(f"图像路径: {first_result.get('image_path', 'N/A')}")
                print(f"布局数据: {'存在' if 'layout' in first_result else '不存在'}")
                print(f"Markdown内容长度: {len(first_result.get('markdown', ''))} 字符")
                
                # 显示Markdown内容的前100个字符
                markdown_content = first_result.get('markdown', '')
                if markdown_content:
                    preview = markdown_content[:100] + "..." if len(markdown_content) > 100 else markdown_content
                    print(f"Markdown预览: {preview}")
            
            # 保存完整响应到文件
            output_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 完整响应已保存到: {output_file}")
            
        except json.JSONDecodeError:
            print("❌ JSON解析失败")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务器正在运行")
        print("💡 提示: 运行 'python main.py --server' 启动服务器")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时 - 服务器响应过慢或处理时间过长")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 Process-PDF接口测试完成!")
    print("=" * 70)
    return True

def test_with_different_parameters(pdf_file_path):
    """测试不同的参数组合"""
    
    print("\n" + "=" * 70)
    print("⚡ 参数组合测试")
    print("=" * 70)
    
    test_cases = [
        {
            'name': '默认参数',
            'params': {'longest_side': '1280'}
        },
        {
            'name': '较小图像',
            'params': {'longest_side': '800'}
        },
        {
            'name': '较大图像',
            'params': {'longest_side': '1920'}
        }
    ]
    
    success_count = 0
    process_url = "http://localhost:8000/process-pdf"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔧 测试 {i}: {test_case['name']}")
        print(f"参数: {test_case['params']}")
        
        try:
            files = {
                'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf')
            }
            
            response = requests.post(process_url, files=files, data=test_case['params'], timeout=30)
            
            if response.status_code == 200:
                success_count += 1
                data = response.json()
                print(f"✅ 成功 - 页数: {data.get('total_pages', 0)}, 耗时: {response.elapsed.total_seconds():.3f}秒")
            else:
                print(f"❌ 失败 - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n📊 参数测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        # 使用默认的t.pdf文件
        pdf_file = "t.pdf"
    
    print("🚀 开始测试PDF处理服务的process-pdf接口")
    print("-" * 70)
    
    # 测试主要功能
    success = test_process_pdf_endpoint(pdf_file)
    
    # 如果主要测试成功，进行参数组合测试
    if success:
        print("\n" + "=" * 70)
        print("🎯 主要测试通过，开始参数组合测试")
        print("=" * 70)
        
        param_success = test_with_different_parameters(pdf_file)
        
        if param_success:
            print("\n🎉 所有测试通过! PDF处理服务运行正常。")
            sys.exit(0)
        else:
            print("\n⚠️  参数组合测试未完全通过")
            sys.exit(1)
    else:
        print("\n❌ Process-PDF接口测试失败")
        sys.exit(1)