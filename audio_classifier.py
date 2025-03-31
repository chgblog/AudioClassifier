import os
import pandas as pd
import google.generativeai as genai
import argparse
from pathlib import Path
import mimetypes
import logging
from tqdm import tqdm
import shutil

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("audio_classifier.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = [
    '.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'
]

def setup_gemini_api(api_key, model_name='gemini-2.0-flash-001', proxy=None):
    """设置Gemini API"""
    try:
        # 配置API密钥
        genai.configure(api_key=api_key)
        
        # 如果提供了代理，设置代理
        if proxy:
            import os
            # 设置HTTP和HTTPS代理环境变量
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy
            logger.info(f"已设置代理: {proxy}")
        
        # 使用指定的模型
        logger.info(f"使用模型: {model_name}")
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        logger.error(f"设置Gemini API时出错: {str(e)}")
        raise

def is_audio_file(file_path):
    """检查文件是否为支持的音频格式"""
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in SUPPORTED_AUDIO_FORMATS

def get_audio_files(directory):
    """遍历目录及子目录获取所有音频文件"""
    audio_files = []
    unsupported_files = []
    
    logger.info(f"开始扫描目录: {directory}")
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_audio_file(file_path):
                audio_files.append(file_path)
            else:
                # 检查是否为其他音频格式但不受支持
                mime_type = mimetypes.guess_type(file_path)[0]
                if mime_type and mime_type.startswith('audio/'):
                    unsupported_files.append((file_path, "不支持的音频格式"))
    
    logger.info(f"找到 {len(audio_files)} 个支持的音频文件")
    logger.info(f"找到 {len(unsupported_files)} 个不支持的音频文件")
    return audio_files, unsupported_files

def analyze_audio_with_gemini(model, audio_path, max_retries=100, retry_delay=60):
    """使用Gemini API分析音频文件，支持重试机制"""
    import time
    
    retries = 0
    while retries <= max_retries:
        try:
            # 读取音频文件
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 构建提示词
            prompt = """
            分析这个音频文件并提供以下信息：
            1. 音频内容：详细描述音频中的声音
            2. 使用场景：这个音效可能适合在哪些场景中使用
            3. 标签：为这个音效生成1-5个标签，用于分类（用逗号分隔）
            
            请按以下格式返回结果：
            音频内容：[详细描述]
            使用场景：[场景描述]
            标签：[标签1, 标签2, ...]
            """
            
            # 调用Gemini API
            response = model.generate_content(
                [
                    prompt,
                    {"mime_type": "audio/mp3", "data": audio_data}
                ]
            )
            
            # 解析响应
            result = response.text
            
            # 提取信息
            content = ""
            scenario = ""
            tags = ""
            
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith("音频内容："):
                    content = line.replace("音频内容：", "").strip()
                elif line.startswith("使用场景："):
                    scenario = line.replace("使用场景：", "").strip()
                elif line.startswith("标签："):
                    tags = line.replace("标签：", "").strip()
            
            return {
                "音频内容": content,
                "使用场景": scenario,
                "标签": tags,
                "失败原因": ""
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"分析音频 {audio_path} 时出错: {error_msg}")
            
            # 检查是否是配额限制错误
            if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "rate" in error_msg.lower():
                retries += 1
                if retries <= max_retries:
                    wait_time = retry_delay
                    logger.info(f"API请求超限制，等待{wait_time}秒后重试 (尝试 {retries}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"达到最大重试次数 ({max_retries})，放弃处理文件: {audio_path}")
            
            return {
                "音频内容": "",
                "使用场景": "",
                "标签": "",
                "失败原因": error_msg
            }

def save_results_to_excel(results, output_path):
    """将结果保存到Excel文件"""
    try:
        # 确保输出路径是绝对路径
        if not os.path.isabs(output_path):
            output_path = os.path.abspath(output_path)
            
        # 创建DataFrame并保存到Excel
        df = pd.DataFrame(results)
        df.to_excel(output_path, index=False)
        logger.info(f"结果已保存到: {output_path}")
        return True
    except ImportError as e:
        if "openpyxl" in str(e):
            logger.error("缺少openpyxl模块，无法保存Excel文件。请安装: pip install openpyxl")
            print("\n错误: 缺少openpyxl模块，无法保存Excel文件。请安装: pip install openpyxl")
        else:
            logger.error(f"保存Excel文件时出错: {str(e)}")
            print(f"\n保存Excel文件时出错: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"保存Excel文件时出错: {str(e)}")
        return False

def extract_main_category(tags):
    """从标签中提取主要分类"""
    if not tags:
        return "未分类"
    
    # 简单地使用第一个标签作为主分类
    tags_list = [tag.strip() for tag in tags.split(',')]
    if tags_list:
        return tags_list[0]
    return "未分类"

def organize_files_by_category(audio_path, category, output_dir):
    """根据分类将音频文件归类到对应文件夹"""
    try:
        # 创建分类目录
        category_dir = os.path.join(output_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        # 获取原始文件名
        file_name = os.path.basename(audio_path)
        
        # 目标文件路径
        target_path = os.path.join(category_dir, file_name)
        
        # 如果目标文件已存在，添加序号
        if os.path.exists(target_path):
            name, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(category_dir, f"{name}_{counter}{ext}")
                counter += 1
        
        # 复制文件到分类目录
        shutil.copy2(audio_path, target_path)
        logger.info(f"已将文件 {file_name} 归类到 {category} 分类")
        
        # 返回新的文件路径
        return target_path
    except Exception as e:
        logger.error(f"归类文件时出错: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='使用Gemini API分析音频文件并生成分类')
    parser.add_argument('--directory', '-d', type=str, required=True, help='音频文件目录路径')
    parser.add_argument('--api_key', '-k', type=str, required=True, help='Gemini API密钥')
    parser.add_argument('--output', '-o', type=str, default='audio_classification_results.xlsx', help='输出Excel文件路径')
    parser.add_argument('--max_retries', '-r', type=int, default=60, help='API请求失败时的最大重试次数')
    parser.add_argument('--retry_delay', '-t', type=int, default=60, help='API请求失败后重试的等待时间(秒)')
    parser.add_argument('--category_dir', '-c', type=str, default='分类音频', help='分类后的音频文件存放目录')
    parser.add_argument('--proxy', '-p', type=str, help='HTTP/HTTPS代理服务器地址，格式如：http://127.0.0.1:7890')
    parser.add_argument('--model', '-m', type=str, default='gemini-2.0-flash-001', help='使用的Gemini模型名称，默认为gemini-2.0-flash-001')
    
    args = parser.parse_args()
    
    # 验证目录是否存在
    if not os.path.isdir(args.directory):
        logger.error(f"目录不存在: {args.directory}")
        return
    
    try:
        # 设置Gemini API
        model = setup_gemini_api(args.api_key, args.model, args.proxy)
        
        # 获取音频文件
        audio_files, unsupported_files = get_audio_files(args.directory)
        
        # 准备结果数据
        results = []
        
        # 确保输出路径是绝对路径
        output_path = args.output
        if not os.path.isabs(output_path):
            output_path = os.path.abspath(output_path)
        
        # 确保分类目录是绝对路径
        category_dir = args.category_dir
        if not os.path.isabs(category_dir):
            category_dir = os.path.abspath(category_dir)
        
        # 创建分类根目录
        os.makedirs(category_dir, exist_ok=True)
        logger.info(f"分类文件将保存到: {category_dir}")
        
        # 分析支持的音频文件
        for i, audio_file in enumerate(tqdm(audio_files, desc="分析音频文件")):
            logger.info(f"正在分析: {audio_file} ({i+1}/{len(audio_files)})")
            analysis = analyze_audio_with_gemini(model, audio_file, args.max_retries, args.retry_delay)
            
            # 提取主分类
            main_category = extract_main_category(analysis["标签"])
            
            # 归类文件
            categorized_path = ""
            if analysis["标签"] and not analysis["失败原因"]:
                categorized_path = organize_files_by_category(audio_file, main_category, category_dir) or ""
            
            results.append({
                "音频文件路径": audio_file,
                "分类后路径": categorized_path,
                "主分类": main_category,
                "音频内容": analysis["音频内容"],
                "使用场景": analysis["使用场景"],
                "标签": analysis["标签"],
                "失败原因": analysis["失败原因"]
            })
            
            # 每分析完一个文件就保存一次结果
            save_results_to_excel(results, output_path)
            logger.info(f"已保存当前进度 ({i+1}/{len(audio_files)})")
        
        # 添加不支持的文件到结果
        if unsupported_files:
            for file_path, reason in unsupported_files:
                results.append({
                    "音频文件路径": file_path,
                    "分类后路径": "",
                    "主分类": "不支持",
                    "音频内容": "",
                    "使用场景": "",
                    "标签": "",
                    "失败原因": reason
                })
            
            # 保存最终结果（包含不支持的文件）
            save_results_to_excel(results, output_path)
        
        logger.info(f"分析完成，最终结果已保存到: {output_path}")
        logger.info(f"分类文件已保存到: {category_dir}")
        print(f"\n分析结果已保存到: {output_path}")
        print(f"分类文件已保存到: {category_dir}")
    
    except Exception as e:
        logger.error(f"程序执行过程中出错: {str(e)}")

if __name__ == "__main__":
    main()