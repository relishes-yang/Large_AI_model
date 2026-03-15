import pandas as pd
import streamlit as st
from utils import dataframe_agent  # 这个utils文件已修改为使用通义千问

def create_chart(input_data, chart_type):
    """根据数据类型创建图表"""
    df_data = pd.DataFrame(input_data["data"], columns=input_data["columns"])
    # 如果第一列是索引，设置为索引
    if len(input_data["columns"]) > 1:
        df_data.set_index(input_data["columns"][0], inplace=True)
    if chart_type == "bar":
        st.bar_chart(df_data)
    elif chart_type == "line":
        st.line_chart(df_data)
    elif chart_type == "scatter":
        st.scatter_chart(df_data)


st.title("💡 通义千问CSV数据分析工具")

with st.sidebar:
    dashscope_api_key = st.text_input("请输入通义千问API Key：", type="password")
    st.markdown("[获取通义千问API Key](https://dashscope.console.aliyun.com/apiKey)")
    st.markdown("### 模型选择")
    model = st.selectbox(
        "选择模型",
        ["qwen-max", "qwen-plus", "qwen-turbo"],
        index=0
    )
    temperature = st.slider("生成随机性", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.number_input("最大生成长度", min_value=50, max_value=4096, value=2048, step=50)

data = st.file_uploader("上传你的数据文件（CSV格式）：", type="csv")
if data:
    st.session_state["df"] = pd.read_csv(data)
    with st.expander("原始数据"):
        st.dataframe(st.session_state["df"])

query = st.text_area("请输入你关于以上表格的问题，或数据提取请求，或可视化要求（支持散点图、折线图、条形图）：")
button = st.button("生成回答")

if button and not dashscope_api_key:
    st.info("请输入你的通义千问API Key")
if button and "df" not in st.session_state:
    st.info("请先上传数据文件")
if button and dashscope_api_key and "df" in st.session_state:
    with st.spinner("通义千问正在思考中，请稍等..."):
        # 传递额外参数给dataframe_agent
        response_dict = dataframe_agent(
            dashscope_api_key,
            st.session_state["df"],
            query,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if "answer" in response_dict:
            st.write(response_dict["answer"])
        if "table" in response_dict:
            st.table(pd.DataFrame(response_dict["table"]["data"],
                                  columns=response_dict["table"]["columns"]))
        if "bar" in response_dict:
            create_chart(response_dict["bar"], "bar")
        if "line" in response_dict:
            create_chart(response_dict["line"], "line")
        if "scatter" in response_dict:
            create_chart(response_dict["scatter"], "scatter")