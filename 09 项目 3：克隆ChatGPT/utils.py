"""
工具函数 - 通义千问 API 调用封装
"""
import os
import dashscope
from dashscope import Generation


def get_qwen_response(messages, model="qwen-plus", temperature=0.7, max_tokens=2048):
    """
    使用通义千问模型生成回复
    
    :param messages: 消息列表，格式为 [{"role": "user/system", "content": "内容"}]
    :param model: 模型名称 (qwen-max/qwen-plus/qwen-turbo)
    :param temperature: 控制生成随机性 (0-1)，越高越随机
    :param max_tokens: 最大输出长度
    :return: 模型生成的文本
    """
    
    # 设置 API Key（从环境变量获取）
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到环境变量 DASHSCOPE_API_KEY，请先配置阿里云百炼 API Key")
    
    # 调用千问 API
    response = Generation.call(
        api_key=api_key,
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
