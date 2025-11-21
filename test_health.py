#!/usr/bin/env python3
"""
测试health接口的脚本
用于验证PDF处理服务的健康状态接口
"""

import requests
import json
import sys
from datetime import datetime

def test_health_endpoint():
    """测试health接口"""
    
    # 服务地址
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/health"
    
    print("=" * 60)
    print("📊 Health接口测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {health_url}")
    print("-" * 60)
    
    try:
        # 发送GET请求
        response = requests.get(health_url, timeout=10)
        
        # 打印响应信息
        print(f"✅ 请求成功!")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response.elapsed.total_seconds():.3f}秒")
        
        # 检查状态码
        if response.status_code == 200:
            print("✅ 状态码: 200 (OK)")
        else:
            print(f"❌ 状态码: {response.status_code} (非200)")
            return False
        
        # 解析JSON响应
        try:
            data = response.json()
            print("✅ JSON解析成功")
            
            # 打印响应数据
            print("\n📋 响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 验证响应字段
            required_fields = ['status', 'service', 'version']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必要字段: {missing_fields}")
                return False
            else:
                print("✅ 所有必要字段都存在")
            
            # 验证具体字段值
            if data.get('status') == 'healthy':
                print("✅ 服务状态: healthy")
            else:
                print(f"❌ 服务状态异常: {data.get('status')}")
                return False
                
            if data.get('service') == 'pdf-processing-service':
                print("✅ 服务名称正确")
            else:
                print(f"❌ 服务名称不匹配: {data.get('service')}")
                return False
                
            print(f"✅ 版本号: {data.get('version')}")
            
        except json.JSONDecodeError:
            print("❌ JSON解析失败")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务器正在运行")
        print("💡 提示: 运行 'python main.py --server' 启动服务器")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时 - 服务器响应过慢")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Health接口测试通过!")
    print("=" * 60)
    return True

def test_multiple_requests():
    """测试多次请求的性能"""
    
    print("\n" + "=" * 60)
    print("⚡ 性能测试 - 连续5次请求")
    print("=" * 60)
    
    health_url = "http://localhost:8000/health"
    response_times = []
    success_count = 0
    
    for i in range(5):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                success_count += 1
                response_time = response.elapsed.total_seconds()
                response_times.append(response_time)
                print(f"请求 {i+1}: ✅ 成功 - {response_time:.3f}秒")
            else:
                print(f"请求 {i+1}: ❌ 失败 - 状态码 {response.status_code}")
        except Exception as e:
            print(f"请求 {i+1}: ❌ 异常 - {e}")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n📊 性能统计:")
        print(f"成功请求: {success_count}/5")
        print(f"平均响应时间: {avg_time:.3f}秒")
        print(f"最快响应: {min_time:.3f}秒")
        print(f"最慢响应: {max_time:.3f}秒")
    
    return success_count == 5

if __name__ == "__main__":
    print("🚀 开始测试PDF处理服务的health接口")
    print("-" * 60)
    
    # 测试单个请求
    success = test_health_endpoint()
    
    # 如果单个请求成功，测试性能
    if success:
        performance_success = test_multiple_requests()
        
        if performance_success:
            print("\n🎉 所有测试通过! 服务运行正常。")
            sys.exit(0)
        else:
            print("\n⚠️  性能测试未完全通过")
            sys.exit(1)
    else:
        print("\n❌ Health接口测试失败")
        sys.exit(1)