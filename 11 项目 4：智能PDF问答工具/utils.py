"""
工具函数 - 通义千问 API 调用封装（PDF问答专用）
"""
import os
import dashscope
from dashscope import Generation


def get_qwen_response_with_context(question, context, model="qwen-plus", temperature=0.7, max_tokens=2048):
    """
    使用通义千问模型基于上下文生成回复
    
    :param question: 用户问题
    :param context: 从 PDF 中提取的相关上下文
    :param model: 模型名称 (qwen-max/qwen-plus/qwen-turbo)
    :param temperature: 控制生成随机性 (0-1)，越高越随机
    :param max_tokens: 最大输出长度
    :return: 模型生成的文本
    """
    
    # 设置 API Key（从环境变量获取）
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到环境变量 DASHSCOPE_API_KEY，请先配置阿里云百炼 API Key")
    
    # 构建提示词
    prompt = f"""请根据以下提供的上下文信息来回答用户的问题。如果上下文中没有相关信息，请直接说明无法从文档中找到答案。

上下文信息：
{context}

用户问题：{question}

请基于以上上下文信息用中文回答用户的问题："""
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": "你是一个专业的文档问答助手。你需要根据提供的文档片段来回答用户的问题，保持答案准确、简洁、专业。如果文档中没有相关信息，请诚实地告诉用户。"},
        {"role": "user", "content": prompt}
    ]
    
    # 调用千问 API
    response = Generation.call(
        api_key="DASHSCOPE_API_KEY",
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        result_format="message"  # 返回格式为 message
    )
    
    # 从响应中提取内容
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        error_msg = f"API 错误：{response.code} - {response.message}"
        print(f"HTTP 返回码：{response.status_code}")
        print(f"错误码：{response.code}")
        print(f"错误信息：{response.message}")
        print("请参考文档：https://help.aliyun.com/model-studio/developer-reference/error-code")
        raise Exception(error_msg)
