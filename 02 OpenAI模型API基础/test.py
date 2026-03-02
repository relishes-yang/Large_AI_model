

# 创建Qwen模型实例
model = Qwen(model="qwen-max")

# 生成回复
response = model.create_completion(prompt="你好，介绍一下你自己")
print(response)