import cv2
import os
import numpy as np
import fitz  # PyMuPDF
import base64
import requests
import pathlib
import shutil
# 动态导入配置，支持直接运行和包导入两种方式
try:
    from ..config.config import DEFAULT_LONGEST_SIDE
except ImportError:
    # 直接运行时使用绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.config import DEFAULT_LONGEST_SIDE

def resize_longest_side(image, longest_side=DEFAULT_LONGEST_SIDE):
    """
    缩放图像，最长的边为指定像素
    
    Args:
        image: 输入的cv2图像对象
        longest_side (int): 最长边的像素大小，默认为1280
        
    Returns:
        缩放后的cv2图像对象
    """
    # 获取原始尺寸
    height, width = image.shape[:2]
    
    # 计算缩放比例
    if width > height:
        # 宽度是长边
        scale = longest_side / width
        new_width = longest_side
        new_height = int(height * scale)
    else:
        # 高度是长边
        scale = longest_side / height
        new_height = longest_side
        new_width = int(width * scale)
    
    # 缩放图像
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    return resized_image

def encode_image_to_base64(image_input):
    """
    将图像编码为Base64字符串，支持文件路径或cv2图像对象
    
    Args:
        image_input (str or numpy.ndarray): 图像文件路径或cv2图像对象
        
    Returns:
        str: Base64编码的图像字符串
        
    Raises:
        TypeError: 如果输入类型不支持
    """
    if isinstance(image_input, str):
        # 输入是文件路径
        with open(image_input, "rb") as file:
            image_bytes = file.read()
            image_data = base64.b64encode(image_bytes).decode("ascii")
        return image_data
    elif hasattr(image_input, 'dtype') and hasattr(image_input, 'shape'):
        # 输入是numpy数组（cv2图像对象）
        success, encoded_image = cv2.imencode('.png', image_input)
        if not success:
            raise ValueError("Failed to encode image to PNG format")
        image_bytes = encoded_image.tobytes()
        image_data = base64.b64encode(image_bytes).decode("ascii")
        return image_data
    else:
        raise TypeError("Unsupported input type. Expected file path (str) or cv2 image object (numpy.ndarray)")

def create_layout_parsing_payload(image_data, file_type=1):
    """
    创建布局解析API的请求负载
    
    Args:
        image_data (str): Base64编码的图像数据或文件URL
        file_type (int): 文件类型，1表示图像文件
        
    Returns:
        dict: API请求负载
    """
    return {
        "file": image_data,
        "fileType": file_type
    }

def call_layout_parsing_api(api_url, payload):
    """
    调用布局解析API
    
    Args:
        api_url (str): API端点URL
        payload (dict): 请求负载
        
    Returns:
        requests.Response: API响应对象
    """
    response = requests.post(api_url, json=payload)
    return response

def process_layout_parsing_result(response):
    """
    处理布局解析API的返回结果
    
    Args:
        response (requests.Response): API响应对象
        
    Returns:
        dict: 解析后的结果数据
    """
    assert response.status_code == 200
    return response.json()["result"]

def pdf_to_images(pdf_input, output_dir="temp_images", dpi=300):
    """
    将PDF文件按页转换为PNG图像（使用PyMuPDF替代pdf2image）
    
    Args:
        pdf_input (str or file-like object): PDF文件路径或文件对象
        output_dir (str): 输出目录
        dpi (int): 图像分辨率（仅为了接口兼容性）
        
    Returns:
        list: 生成的图像文件路径列表
    """
    # 创建输出目录
    pathlib.Path(output_dir).mkdir(exist_ok=True)
    
    image_paths = []
    
    # 使用PyMuPDF打开PDF - 支持文件路径或文件对象
    if isinstance(pdf_input, str):
        # 输入是文件路径
        doc = fitz.open(pdf_input)
    else:
        # 输入是文件对象
        # 先将文件内容读取到内存中，然后使用fitz.open打开
        pdf_content = pdf_input.read()
        doc = fitz.open("pdf", pdf_content)
    
    for i in range(len(doc)):
        # 获取页面
        page = doc.load_page(i)
        
        # 将页面转换为图像（矩阵）
        mat = fitz.Matrix(2.0, 2.0)  # 缩放因子，2.0表示200%质量
        pix = page.get_pixmap(matrix=mat)
        
        # 保存图像
        image_path = pathlib.Path(output_dir) / f"page_{i+1:03d}.png"
        pix.save(str(image_path))
        image_paths.append(str(image_path))
        
        print(f"Saved page {i+1} as {image_path}")
    
    doc.close()
    return image_paths

def extract_markdown_from_result(result):
    """
    从API结果中提取markdown内容
    
    Args:
        result (dict): API返回的结果
        
    Returns:
        dict: 包含markdown内容的字典，格式为 {'pageX': 'markdown内容'}
    """
    markdown_dict = {}
    
    for i, res in enumerate(result["layoutParsingResults"]):
        page_key = f"page{i+1}"
        markdown_dict[page_key] = res["markdown"]["text"]
    
    return markdown_dict

def process_pdf_file(pdf_input, api_url, longest_side=1280):
    """
    处理PDF文件：转换、调整大小、解析布局，直接返回markdown内容
    
    Args:
        pdf_input (str or file-like object): PDF文件路径或文件对象
        api_url (str): 布局解析API URL
        longest_side (int): 最长边像素大小
        
    Returns:
        dict: 包含所有页面markdown内容的字典，格式为 {'page1': '内容', 'page2': '内容', ...}
    """
    # 创建临时图像目录
    temp_dir = "temp_pdf_images"
    
    try:
        # 1. 转换PDF为图像
        print(f"Converting PDF to images...")
        image_paths = pdf_to_images(pdf_input, temp_dir)
        print(f"✓ PDF转换完成，共 {len(image_paths)} 页")
        
        all_markdowns = []
        
        for i, image_path in enumerate(image_paths):
            print(f"\n--- 处理第 {i+1}/{len(image_paths)} 页 ---")
            print(f"Processing image: {image_path}")
            
            # 2. 读取图像并调整大小
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ 读取图像失败: {image_path}")
                continue
                
            original_size = image.shape[:2]
            resized_image = resize_longest_side(image, longest_side)
            resized_size = resized_image.shape[:2]
            print(f"✓ 图像调整大小: {original_size} → {resized_size}")
            
            # 3. 编码为Base64
            image_data = encode_image_to_base64(resized_image)
            print(f"✓ Base64编码完成，数据长度: {len(image_data)} 字符")
            
            # 4. 创建负载并调用API
            payload = create_layout_parsing_payload(image_data)
            print(f"✓ 请求负载创建完成")
            
            response = call_layout_parsing_api(api_url, payload)
            print(f"✓ API调用成功，状态码: {response.status_code}")
            
            # 5. 处理结果并提取markdown
            result = process_layout_parsing_result(response)
            page_markdowns = extract_markdown_from_result(result)
            
            # 显示提取的markdown统计信息
            for page_name, content in page_markdowns.items():
                char_count = len(content)
                line_count = content.count('\n') + 1
                print(f"✓ 提取 {page_name}: {char_count} 字符, {line_count} 行")
            
            # 合并到总结果中 - 生成要求的JSON格式
            for page_name, content in page_markdowns.items():
                page_json = {
                    "page": i + 1,
                    "ocrContent": {
                        "backend": "pipeline",
                        "version": "2.5.4",
                        "results": {
                            "image": {
                                "md_content": content
                            }
                        }
                    }
                }
                all_markdowns.append(page_json)
            print(f"✓ 第 {i+1} 页处理完成")
            
        print(f"\n🎉 所有页面处理完成!")
        print(f"总页数: {len(all_markdowns)}")
        total_chars = sum(len(page["ocrContent"]["results"]["image"]["md_content"]) for page in all_markdowns)
        print(f"总字符数: {total_chars}")
        
        # 转换为JSON字符串
        import json
        json_output = json.dumps(all_markdowns, ensure_ascii=False, indent=2)
        print(f"✓ JSON输出完成，共 {len(json_output)} 字符")
        print(f"JSON输出预览:\n{json_output[:20000]}...")  # 显示前200个字符
        return json_output
        
    finally:
        # 清理临时文件
        if pathlib.Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


