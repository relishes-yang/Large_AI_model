from openai import OpenAI

# 这是Qwen的OpenAI兼容API调用方式
client = OpenAI()

response = client.chat.completions.create(
    model="qwen-max",
    messages=[
        {"role": "user", "content": "你好，介绍一下你自己"}
    ]
)
print(response.choices[0].message.content)