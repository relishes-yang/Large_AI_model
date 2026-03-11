"""
克隆ChatGPT - 使用通义千问 API
需要在环境变量中配置 DASHSCOPE_API_KEY
"""
import os
import streamlit as st
from dashscope import Generation
from utils import get_qwen_response

# 设置页面配置
st.set_page_config(
    page_title="ChatGPT 克隆（千问版）",
    page_icon="🤖",
    layout="wide"
)

# 标题
st.title("🤖 ChatGPT 克隆（通义千问版）")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    
    # 模型选择
    model = st.selectbox(
        "选择模型",
        ["qwen-turbo", "qwen-plus", "qwen-max"],
        index=1
    )
    
    # 温度参数
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    
    # 最大 token 数
    max_tokens = st.slider("Max Tokens", 512, 4096, 2048, 256)
    
    # 清空对话按钮
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.info("💡 提示：需要在阿里云百炼平台获取 API Key")

# 初始化会话状态中的消息列表
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入框
if prompt := st.chat_input("请输入您的问题..."):
    # 添加用户消息到历史记录
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成 AI 回复
    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考中..."):
            try:
                # 构建完整的消息历史
                messages_for_api = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + st.session_state.messages
                
                # 调用千问 API
                response = get_qwen_response(
                    messages=messages_for_api,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # 显示 AI 回复
                st.markdown(response)
                
                # 添加 AI 回复到历史记录
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
            except Exception as e:
                st.error(f"❌ 错误：{str(e)}")
                st.info("💡 请检查是否已配置环境变量 DASHSCOPE_API_KEY")
