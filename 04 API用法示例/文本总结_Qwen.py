import os
import dashscope
from dashscope import Generation

# 初始化模型（使用 Qwen-Max，效果最强）
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


def get_qwen_response(prompt, model="qwen-max"):
    """
    使用通义千问模型生成回复
    :param prompt: 提示词
    :param model: 模型名称 (qwen-max/qwen-plus/qwen-turbo)
    :return: 模型生成的文本
    """
    response = Generation.call(
        model=model,
        prompt=prompt,
        temperature=0.7,  # 控制生成随机性 (0-1)
        top_p=0.8,  # 采样概率阈值
        max_tokens=2048  # 最大输出长度
    )

    # 从响应中提取内容
    if response.status_code == 200:
        return response.output.text
    else:
        raise Exception(f"API Error: {response.code} - {response.message}")


# 原始产品评论
product_review = """
我上个月买的这个多功能蓝牙耳机。它的连接速度还挺快，而且兼容性强，无论连接手机还是笔记本电脑，基本上都能快速配对上。
音质方面，中高音清晰，低音效果震撼，当然这个价格来说一分钱一分货吧，毕竟也不便宜。
耳机的电池续航能力不错，单次充满电可以连续使用超过8小时。
不过这个耳机也有一些我不太满意的地方。首先是在长时间使用后，耳廓有轻微的压迫感，这可能是因为耳套的材料较硬。总之我感觉戴了超过4小时后耳朵会有点酸痛，需要摘下休息下。
而且耳机的防水性能不是特别理想，在剧烈运动时的汗水防护上有待加强。
最后是耳机盒子的开合机制感觉不够紧致，有时候会不小心打开。
"""

# 生成提示词
product_review_prompt = f"""
你的任务是为用户对产品的评价生成简要总结。
请把总结主要分为两个方面，产品的优点，以及产品的缺点，并以Markdown列表形式展示。
用户的评价内容会以三个#符号进行包围。

###
{product_review}
###
"""

# 调用千问模型
response = get_qwen_response(product_review_prompt)

# 输出结果
print(response)