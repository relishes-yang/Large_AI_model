import streamlit as st
from langchain_community.llms import Qwen
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.callbacks import get_openai_callback
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="📑 通义千问PDF智能问答", layout="wide")

st.title("📑 通义千问PDF智能问答")

with st.sidebar:
    st.markdown("### 通义千问API配置")
    dashscope_api_key = st.text_input("请输入通义千问API Key：", type="password",
                                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    st.markdown("[获取通义千问API Key](https://dashscope.console.aliyun.com/apiKey)")

    st.markdown("### 模型选择")
    model = st.selectbox(
        "选择模型",
        ["qwen-max", "qwen-plus", "qwen-turbo"],
        index=0
    )

    st.markdown("### 其他设置")
    temperature = st.slider("生成随机性", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.number_input("最大生成长度", min_value=50, max_value=4096, value=2048, step=50)

if "memory" not in st.session_state:
    st.session_state["memory"] = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )

uploaded_file = st.file_uploader("上传你的PDF文件：", type="pdf")
question = st.text_input("对PDF的内容进行提问", disabled=not uploaded_file)

if uploaded_file and question and not dashscope_api_key:
    st.info("请输入你的通义千问API Key")

if uploaded_file and question and dashscope_api_key:
    with st.spinner("通义千问正在思考中，请稍等..."):
        response = qa_agent(
            dashscope_api_key,
            st.session_state["memory"],
            uploaded_file,
            question,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    st.write("### 答案")
    st.write(response["answer"])
    st.session_state["chat_history"] = response["chat_history"]

if "chat_history" in st.session_state:
    with st.expander("历史消息"):
        for i in range(0, len(st.session_state["chat_history"]), 2):
            human_message = st.session_state["chat_history"][i]
            ai_message = st.session_state["chat_history"][i + 1]
            st.write(f"**用户**: {human_message.content}")
            st.write(f"**AI**: {ai_message.content}")
            if i < len(st.session_state["chat_history"]) - 2:
                st.divider()


def qa_agent(dashscope_api_key, memory, uploaded_file, question, model="qwen-max", temperature=0.7, max_tokens=2048):
    # 保存上传的文件到临时位置
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 加载PDF文档
    loader = PyPDFLoader("temp.pdf")
    documents = loader.load()

    # 文本分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    texts = text_splitter.split_documents(documents)

    # 创建向量数据库
    embeddings = DashScopeEmbeddings(
        model="bge-large-zh",
        dashscope_api_key=dashscope_api_key,
    )
    vectorstore = FAISS.from_documents(texts, embeddings)

    # 创建检索器
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}
    )

    # 创建Qwen模型
    llm = Qwen(
        model=model,
        dashscope_api_key=dashscope_api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )

    # 创建RetrievalQA链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    # 执行问答
    result = qa_chain(question)

    # 保存对话历史
    chat_history = []
    if memory:
        chat_history = memory.load_memory_variables({})["chat_history"]
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=result["result"]))
        memory.save_context({"input": question}, {"output": result["result"]})

    return {
        "answer": result["result"],
        "chat_history": chat_history
    }