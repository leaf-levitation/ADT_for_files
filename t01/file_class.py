import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import OPENAI_API_KEY
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from pathlib import Path

llm_default = ChatOpenAI(
        model="qwen3.5-plus",
        api_key=OPENAI_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

def create_bot(llm=llm_default, sys_prompt=''):
    """创建一个带消息历史的LangChain对话机器人。

    创建一个基于RunnableWithMessageHistory的对话链，支持保持会话历史
    记录，能够根据上下文进行多轮对话。

    Args:
        llm: 已配置好的语言模型实例，默认为预配置的通义千问模型
        sys_prompt: 系统提示词，用于指导模型的行为，默认为空字符串

    Returns:
        RunnableWithMessageHistory: 配置好的可运行对话链，支持会话管理

    Example:
        >>> bot = create_bot(sys_prompt="你是一个有用的助手")
        >>> response = bot.invoke({"input": "你好"}, 
        ...     config={"configurable": {"session_id": "123"}})
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system",sys_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human","{input}")
    ])
    parser = StrOutputParser()
    chain = prompt | llm | parser
    store = {}

    def get_session_history(session_id):
        return store.setdefault(session_id,ChatMessageHistory())

    return RunnableWithMessageHistory(
        runnable=chain,
        get_session_history=get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )

class runnable_file:
    """文件树节点类，用于以树形结构组织和管理文件。

    该类实现了一个文件树节点，可以存储文件内容，并支持构建目录树结构，
    递归遍历以及大语言模型文件处理功能。

    Attributes:
        name (str): 文件/目录名称
        content (str): 文件内容，对于目录通常存储content.txt的内容
        parent (Optional[runnable_file]): 父节点引用，根节点为None
        children (List[runnable_file]): 子节点列表
    """
    def __init__(self, name: str, content: str = '',  parent: 'runnable_file' = None):
        """初始化文件树节点。

        Args:
            name: 文件/目录名称
            content: 文件内容，默认为空字符串
            parent: 父节点引用，默认为None
        """
        self.name = name
        self.content = content
        self.parent = parent
        self.children: list['runnable_file'] = []
        
    def add_child(self, child: 'runnable_file'):
        """添加子节点到当前节点。

        将子节点的父引用设置为当前节点，并添加到子节点列表中。

        Args:
            child: 要添加的子节点
        """
        child.parent = self
        self.children.append(child)
        
    def analyzed_by(self, f: 'runnable_file', task_id, output_dir: str = None) -> str:
        """使用给定的提示文件处理当前文件内容，并保存结果。

        使用LangChain的对话链结合大语言模型处理当前文件内容，根据提示文件中的
        系统提示对输入内容进行分析处理，并将结果保存到文件中。

        Args:
            f: 包含系统提示的runnable_file对象
            task_id: 会话ID，用于消息历史记录
            output_dir: 可选的输出目录路径，如果不提供则使用当前工作目录

        Returns:
            str: 处理后的结果内容

        Note:
            如果实例包含dir属性，则默认输出到self.dir的父目录，否则输出到当前工作目录
        """
        system_input = f.content
        user_input = self.content

        bot = create_bot(llm=llm_default, sys_prompt=system_input)
        session_id = task_id

        response = bot.invoke(
            {"input": user_input}, 
            config={"configurable": {"session_id": session_id}}
        )
        
        if output_dir is None:
            if hasattr(self, 'dir') and self.dir:
                output_path = os.path.join(
                    os.path.abspath(os.path.join(self.dir, '..')), 
                    f'{self.name}_processed.txt'
                )
            else:
                output_path = f'{self.name}_processed.txt'
        else:
            output_path = os.path.join(output_dir, f'{self.name}_processed.txt')
            
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(response)
        
        return response

    @staticmethod
    def build_tree(root_dir: str, parent: 'runnable_file'= None) -> 'runnable_file':
        """从文件夹递归构建runnable_file树。

        读取指定根文件夹，每个文件夹自动读取其下的content.txt文件作为节点内容，
        并递归处理所有子文件夹，构建出完整的文件树结构。

        Args:
            root_dir: 要构建树的根文件夹路径
            parent: 父节点引用，默认为None（根节点）

        Returns:
            runnable_file: 构建好的根节点

        Note:
            每个文件夹下应该有一个content.txt文件用于存储该节点的内容。
            该方法会递归处理所有子文件夹。
        """
        root_path = Path(root_dir)
        dir_name = root_path.name
        content_path = os.path.join(root_dir, "content.txt")
        content = ""
        if os.path.exists(content_path):
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        node = runnable_file(dir_name, content, parent)

        for item in root_path.iterdir():
            if item.is_dir():
                next_dir = os.path.join(root_dir, item.name)
                child = runnable_file.build_tree(next_dir, node)
                node.add_child(child)
        return node
    
    def build_folder(self, output_dir: str) -> None:
        """将runnable_file树递归输出为文件夹结构。

        在指定输出目录创建对应于当前节点的文件夹，将节点内容写入content.txt，
        并递归处理所有子节点生成子文件夹结构。

        Args:
            output_dir: 输出的根文件夹路径

        Note:
            如果目录不存在，会自动创建。输出结构完全对应于输入的树结构。
        """
        if self.parent:
            current_dir = os.path.join(output_dir, self.name)
        else:
            current_dir = output_dir

        os.makedirs(current_dir, exist_ok=True)
        content_path = os.path.join(current_dir, 'content.txt')
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        
        for child in self.children:
            if self.parent is None:
                child_output_dir = output_dir
            else:
                child_output_dir = current_dir
            child.build_folder(child_output_dir)
