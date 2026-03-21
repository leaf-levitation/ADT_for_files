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

llm_default = ChatOpenAI(
        model="qwen3.5-plus",
        api_key=OPENAI_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

def create_bot(llm=llm_default,sys_prompt=''):
    """
    :param sys_prompt: 系统提示词
    :param llm: 已配置好的语言模型实例
    :return:
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

class ADT_for_file:
    class runnable_file:
        def __init__(self,dir:str):
            self.dir=dir
            for i in range(len(dir)-1,0,-1):
                if dir[i]=='.':
                    index_1=i
                if dir[i]=='/':
                    index_2=i
                    break
            self.name=dir[index_2+1:index_1] if index_1 and index_2 else 0
            
        def fetch_content(self):
            with open(self.dir,'r',encoding='utf-8') as f:
                content=f.read()
            return content
        
        def analyzed_by(self,f,task_id):
            system_input = f.fetch_content()
            user_input=self.fetch_content()

            bot=create_bot(sys_prompt=system_input)
            session_id = task_id

            response = bot.invoke({"input":user_input},config={"configurable":{"session_id":session_id}})
            output_dir = os.path.join(os.path.abspath(os.path.join(self.dir,'..')),f'{self.name}_processed.txt')
            with open(output_dir,'w',encoding='utf-8') as file:
                file.write(response)


    def __init__(self):
        self.content=[]

    def insert(self,f:runnable_file):
        self.content.append(f)
    def search(self,key):
        result=[]
        for f in self.content:
            if f.name==key:
                result.append(f.dir)
        return result
    
test=ADT_for_file()
dir_1='C:/Users/31360/Desktop/非实体项目/ADT_for_files/t01/files/alphaschool.txt'
f_1=test.runnable_file(dir_1)
dir_2='C:/Users/31360/Desktop/非实体项目/ADT_for_files/t01/files/differnology.txt'
f_2=test.runnable_file(dir_2)
test.insert(f_1)
test.insert(f_2)
f_1.analyzed_by(f_2,1)
