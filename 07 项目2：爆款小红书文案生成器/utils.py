# 修复后的完整代码（直接复制即可运行）
from prompt_template import system_template_text, user_template_text
from langchain_community.chat_models import Qwen  # 通义千问官方集成
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from xiaohongshu_model import Xiaohongshu
import os  # 修正：原错误写成了 ospip


def generate_xiaohongshu(theme, qwen_api_key=None):
    """
    使用通义千问生成小红书文案（国内合规方案）

    依赖安装（必须执行！）：
    pip install langchain-community dashscope
    """
    # 获取API Key（优先使用传入的，其次环境变量）
    api_key = qwen_api_key or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "❌ 未提供通义千问API Key！\n"
            "请通过以下任一方式设置：\n"
            "1. 设置环境变量：export DASHSCOPE_API_KEY='sk-xxx' (Linux/Mac)\n"
            "2. 或在代码中传入：generate_xiaohongshu('主题', 'sk-xxx')"
        )

    # 初始化模型（使用国内可用的qwen-max）
    model = ChatQianwen(
        model_name="qwen-max",
        dashscope_api_key=api_key,
        temperature=0.7,
        max_tokens=1024
    )

    # 构建提示词链
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template_text),
        ("user", user_template_text)
    ])

    output_parser = PydanticOutputParser(pydantic_object=Xiaohongshu)
    chain = prompt | model | output_parser

    # 生成内容
    result = chain.invoke({
        "parser_instructions": output_parser.get_format_instructions(),
        "theme": theme
    })

    return result


# ============ 使用示例 ============
if __name__ == "__main__":
    try:
        # 从环境变量获取API Key（推荐安全方式）
        result = generate_xiaohongshu("夏日防晒攻略")

        print("\n" + "=" * 50)
        print("✅ 生成成功！小红书文案如下：")
        print("=" * 50)
        print(f"📌 标题: {result.title}")
        print(f"📝 正文: {result.content}")
        print(f"🏷️ 标签: #{' #'.join(result.tags)}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"❌ 生成失败: {str(e)}\n"
              "请检查：\n"
              "1. 是否已安装依赖（pip install langchain-community dashscope）\n"
              "2. 是否正确设置DASHSCOPE_API_KEY环境变量\n"
              "3. API Key是否有效（阿里云百炼平台获取）")