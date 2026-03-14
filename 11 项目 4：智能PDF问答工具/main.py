"""
智能PDF问答工具 - 使用通义千问 API
需要在环境变量中配置 DASHSCOPE_API_KEY
"""
import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from dashscope import Generation
from utils import get_qwen_response_with_context

# 设置页面配置
st.set_page_config(
    page_title="智能PDF问答工具（千问版）",
    page_icon="📚",
    layout="wide"
)

# 标题
st.title("📚 智能PDF问答工具（通义千问版）")

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
    
    # 文本分块大小
    chunk_size = st.slider("文本分块大小", 100, 1000, 500, 100)
    
    # 文本分块重叠
    chunk_overlap = st.slider("文本分块重叠", 0, 200, 40, 10)
    
    st.markdown("---")
    st.info("💡 提示：需要在阿里云百炼平台获取 API Key")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None

# 文件上传
uploaded_file = st.file_uploader("上传 PDF 文件", type=["pdf"])

if uploaded_file is not None:
    # 如果文件发生变化，重新处理
    if uploaded_file.name != st.session_state.processed_file:
        with st.spinner("正在处理 PDF 文件..."):
            try:
                # 保存临时文件
                temp_file_path = f"./temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 加载 PDF 文档
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()
                
                # 分割文本
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n", "。", "！", "？", "，", "、", ""]
                )
                texts = text_splitter.split_documents(docs)
                
                # 创建嵌入向量和向量存储
                with st.spinner("正在创建索引..."):
                    embeddings_model = OpenAIEmbeddings()
                    db = FAISS.from_documents(texts, embeddings_model)
                    st.session_state.vector_store = db
                
                # 清理临时文件
                os.remove(temp_file_path)
                
                st.session_state.processed_file = uploaded_file.name
                st.success(f"✅ PDF 文件处理完成：{uploaded_file.name}")
                
                # 清空之前的对话
                st.session_state.messages = []
                
            except Exception as e:
                st.error(f"❌ 处理 PDF 文件时出错：{str(e)}")
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入框
if prompt := st.chat_input("请输入您的问题..."):
    if st.session_state.vector_store is None:
        st.error("请先上传 PDF 文件！")
    else:
        # 添加用户消息到历史记录
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考中..."):
                try:
                    # 从向量存储中检索相关文档
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                    relevant_docs = retriever.get_relevant_documents(prompt)
                    
                    # 组上下文信息
                    context = "\n\n".join([doc.page_content for doc in relevant_docs])
                    
                    # 调用千问 API
                    response = get_qwen_response_with_context(
                        question=prompt,
                        context=context,
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
                    
                    # 显示参考来源
                    with st.expander("查看参考来源"):
                        for i, doc in enumerate(relevant_docs, 1):
                            st.markdown(f"**来源 {i}:**")
                            st.text(doc.page_content[:200] + "...")
                    
                except Exception as e:
                    st.error(f"❌ 错误：{str(e)}")
                    st.info("💡 请检查是否已配置环境变量 DASHSCOPE_API_KEY")
