from langchain.chains import ConversationChain
from langchain_community.llms import Qwen
from langchain.memory import ConversationBufferMemory
import os


def get_chat_response(prompt, memory, openai_api_key):
    # 注意：这里openai_api_key实际是通义千问的API Key
    model = Qwen(
        model="qwen-max",  # 通义千问旗舰模型
        dashscope_api_key=openai_api_key,  # 通义千问API Key
        temperature=0.7,  # 可调整生成随机性
        max_tokens=2048
    )
    chain = ConversationChain(llm=model, memory=memory)
    response = chain.invoke({"input": prompt})
    return response["response"]


# 使用示例
if __name__ == "__main__":
    # 通义千问API Key需设置在环境变量中
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")

    memory = ConversationBufferMemory(return_messages=True)
    print(get_chat_response("牛顿提出过哪些知名的定律？", memory, api_key))
    print(get_chat_response("我上一个问题是什么？", memory, api_key))