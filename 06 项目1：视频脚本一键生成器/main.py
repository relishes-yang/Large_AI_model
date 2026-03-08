import streamlit as st
from utils import generate_script  # 确保 utils.py 已更新为 Qwen + 百度百科版本

st.title("🎬 视频脚本生成器（通义千问版）")

with st.sidebar:
    # 修改为阿里云 DashScope API 密钥输入
    dashscope_api_key = st.text_input("请输入阿里云 DashScope API 密钥：", type="password")
    st.markdown("[获取阿里云 DashScope API 密钥](https://dashscope.aliyun.com/)")  # 更新链接

subject = st.text_input("💡 请输入视频的主题")
video_length = st.number_input("⏱️ 请输入视频的大致时长（单位：分钟）", min_value=0.1, step=0.1)
creativity = st.slider("✨ 请输入视频脚本的创造力（数字小说明更严谨，数字大说明更多样）",
                       min_value=0.0, max_value=1.0, value=0.2, step=0.1)
submit = st.button("生成脚本")

if submit and not dashscope_api_key:
    st.info("请输入你的阿里云 DashScope API 密钥")
    st.stop()
if submit and not subject:
    st.info("请输入视频的主题")
    st.stop()
if submit and video_length < 0.1:
    st.info("视频长度需要大于或等于0.1")
    st.stop()
if submit:
    with st.spinner("AI正在思考中，请稍等..."):
        # 调用 generate_script，传入 dashscope_api_key
        search_result, title, script = generate_script(subject, video_length, creativity, dashscope_api_key)
    st.success("视频脚本已生成！")
    st.subheader("🔥 标题：")
    st.write(title)
    st.subheader("📝 视频脚本：")
    st.write(script)
    with st.expander("🔍 百度百科搜索结果"):  # 建议将“维基百科”改为“百度百科”
        st.info(search_result)