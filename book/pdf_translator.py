import sys
import os
import argparse
import concurrent.futures
from functools import partial

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import OPENAI_API_KEY
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    从PDF文件中按页提取文本
    :param pdf_path: PDF文件路径
    :return: 每页文本列表
    """
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
        else:
            pages_text.append("")  # 处理空白页
    return pages_text

def create_translation_chain(llm):
    """
    创建翻译链
    :param llm: 语言模型实例
    :return: 翻译链
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
将文档内容译为中文。
这是本书翻译工作的一部分，请遵守以下规范：
1.章节标题使用一级标题，小节标题使用二级标题，定理（推论、注记）使用###数字序号（如###1.3），后空一行写具体内容。
2.仅输出文本，不要有任何多余的输出。
3.页眉（通常是你读到的第一行内容）使用引用方式标出，它们不是标题。
"""),
        ("human", "{input_text}")
    ])
    parser = StrOutputParser()
    chain = prompt | llm | parser
    return chain

def translate_page(args, translation_chain):
    """
    翻译单页文本（用于多线程）
    :param args: (页码, 页面文本)
    :param translation_chain: 翻译链实例
    :return: (页码, 格式化翻译内容)
    """
    i, page_text = args
    if not page_text.strip():
        print(f"跳过空白页 {i}")
        return (i, f"## 第 {i} 页\n\n*[空白页]*\n")
    
    try:
        print(f"正在翻译第 {i} 页...")
        translation = translation_chain.invoke({"input_text": page_text})
        return (i, f"{translation}\n")
    except Exception as e:
        print(f"翻译第 {i} 页时出错: {e}")
        return (i, f"第 {i} 页*[翻译失败]*\n---\n")


def process_pdf(pdf_path, output_dir="book_translation", max_workers=10):
    """
    处理PDF文件：拆分、翻译并输出为单个Markdown文件
    :param pdf_path: 输入PDF文件路径
    :param output_dir: 输出目录
    :param max_workers: 最大并发数，默认不超过10
    :return: 输出文件路径
    """
    # 限制最大并发数不超过10
    max_workers = min(max_workers, 10)
    
    llm = ChatOpenAI(
        model="qwen3.5-flash",
        api_key=OPENAI_API_KEY,
        base_url="https://batch.dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # 创建翻译链
    translation_chain = create_translation_chain(llm)
    
    # 提取每页文本
    print(f"正在从PDF提取文本: {pdf_path}")
    pages = extract_text_from_pdf(pdf_path)
    print(f"共提取 {len(pages)} 页，使用 {max_workers} 个并发任务")
    
    # 准备翻译任务
    page_tasks = [(i+1, text) for i, text in enumerate(pages)]
    
    # 使用线程池并发翻译
    translated_content = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        translate_page_with_chain = partial(translate_page, translation_chain=translation_chain)
        results = list(executor.map(translate_page_with_chain, page_tasks))
    
    # 按页码排序结果
    results.sort(key=lambda x: x[0])
    translated_content = [content for (_, content) in results]
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_filename = f"{base_name}_translated.md"
    output_path = os.path.join(output_dir, output_filename)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 合并所有内容并写入文件
    full_content = f"# {base_name} 翻译\n\n" + "\n".join(translated_content)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"\n翻译完成! 结果已保存到: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='PDF书籍翻译工具，按页码拆分并翻译（支持并发翻译）')
    parser.add_argument('pdf_path', type=str, help='输入PDF文件的路径')
    parser.add_argument('--workers', '-w', type=int, default=10, help='最大并发数（不超过10，默认10）')
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"错误: 文件 {args.pdf_path} 不存在")
        sys.exit(1)
    
    # 检查文件扩展名
    if not args.pdf_path.lower().endswith('.pdf'):
        print(f"错误: 输入文件必须是PDF格式")
        sys.exit(1)
    
    # 限制并发数
    if args.workers > 10:
        print(f"警告: 并发数不能超过10，已自动调整为10")
        args.workers = 10
    
    # 开始处理
    process_pdf(args.pdf_path, max_workers=args.workers)

if __name__ == '__main__':
    main()