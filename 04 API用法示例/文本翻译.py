"""
视频教程使用的是openai国内无法使用，自己网上找的换用千问调用，需要在run中配置环境变量DASHSCOPE_API_KEY
"""
import dashscope
from dashscope import Generation

# 设置模型参数（使用Qwen-Max，性能最强的模型）
MODEL_NAME = 'qwen-max'

def get_qwen_response(prompt, model=MODEL_NAME):
    """调用Qwen模型获取响应"""
    response = Generation.call(
        model=model,
        prompt=prompt,
        temperature=0.0,  # 降低随机性确保输出稳定
        top_p=0.8
    )
    if response.status_code == 200:
        return response.output.text.strip()
    else:
        raise Exception(f"API Error: {response.code} - {response.message}")

# 翻译提示词模板
translate_prompt = """
请你充当一家外贸公司的翻译，你的任务是对来自各国家用户的消息进行翻译。
我会给你一段消息文本，请你首先判断消息是什么语言，比如法语。然后把消息翻译成中文。
翻译时请尽可能保留文本原本的语气。输出内容不要有任何额外的解释或说明。

输出格式为:
============
原始消息（<文本的语言>）：
<原始消息>
翻译消息：
<翻译后的文本内容>
============
来自用户的消息内容会以三个#符号进行包围。
###
{message}
###
"""

# 获取用户输入
message = input("请输入需要翻译的消息：")

# 调用Qwen模型进行翻译
response = get_qwen_response(translate_prompt.format(message=message))

# 打印结果
print(response)