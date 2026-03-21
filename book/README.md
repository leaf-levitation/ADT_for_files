# PDF书籍翻译工具

使用LangChain和大语言模型将PDF书籍按页码拆分并翻译的工作流。

## 功能特性

- 自动按页码拆分PDF文件
- 逐页提取文本
- 使用LangChain和大语言模型进行翻译
- 输出格式清晰的Markdown文件，包含原文和译文对照
- 保持原书页码结构

## 安装依赖

项目使用uv管理依赖：

```bash
# 初始化项目（已完成）
uv init

# 安装PyPDF2
uv add PyPDF2
```

所有主要依赖（langchain、langchain-openai等）已经在requirements.txt中。

## 使用方法

```bash
cd 项目根目录
python book_translation/pdf_translator.py <path_to_your_pdf_file>
```

参数说明：
- `<path_to_your_pdf_file>`: 输入PDF文件的路径，必须是PDF格式文件

## 输出

翻译结果会保存在 `book_translation/` 目录下，文件名为 `{原书名}_translated.md`，格式为：

```markdown
# {原书名} 翻译

## 第 1 页

### 原文

```
[原文内容]
```

### 译文

[译文内容]

---

...
```

## 配置说明

参考 `t01/s05_practice.py` 的配置：

- 使用 `deepseek-chat` 模型
- API配置从项目根目录的 `config.py` 中读取 `OPENAI_API_KEY`
- base_url 设置为 `https://api.deepseek.com`

## 依赖

- Python 3.8+
- PyPDF2
- langchain
- langchain-openai
- python-dotenv
```
<task_progress>
- [x] 分析项目结构和需求
- [x] 创建PDF拆分和翻译的主程序
- [x] 实现PDF文本提取功能
- [x] 实现基于LangChain的翻译功能
- [x] 实现输出到Markdown文件功能
- [x] 检查uv环境
- [x] 确认PyPDF2已安装
- [x] 初始化uv项目
- [x] 添加依赖
- [x] 创建README说明文档
- [ ] 测试完整工作流
</task_progress>
</write_to_file>

"C:\Users\31360\Downloads\Real Analysis(Stein)_3.pdf"