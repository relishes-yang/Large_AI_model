from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
import requests
from bs4 import BeautifulSoup
import os
import time
import urllib.parse


class BaiduBaikeAPIWrapper:
    """
    百度百科搜索工具（非官方，通过爬虫实现）
    用于根据关键词搜索百度百科，并返回词条摘要。
    """

    def __init__(self, lang="zh", top_k_results=1):
        self.lang = lang
        self.top_k_results = top_k_results
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _search_baike(self, query: str) -> str:
        """搜索百度百科并返回第一个相关词条的摘要"""
        try:
            # 第一步：搜索词条，获取词条URL
            search_url = f"https://baike.baidu.com/search?word={urllib.parse.quote(query)}"
            resp = requests.get(search_url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return f"搜索请求失败，状态码：{resp.status_code}"

            soup = BeautifulSoup(resp.text, 'lxml')

            # 查找搜索结果中的第一个词条链接
            result_items = soup.select('a.result-title')
            if not result_items:
                return f"未找到与“{query}”相关的百度百科词条。"

            # 获取第一个词条的真实URL（可能是相对路径）
            first_item = result_items[0]
            href = first_item.get('href', '')
            if href.startswith('/item/'):
                item_url = f"https://baike.baidu.com{href}"
            else:
                item_url = href

            # 第二步：进入词条页面，提取摘要
            return self._fetch_summary(item_url, query)

        except requests.exceptions.Timeout:
            return f"百度百科搜索超时：{query}"
        except Exception as e:
            return f"百度百科搜索出错：{str(e)}"

    def _fetch_summary(self, url: str, query: str) -> str:
        """从词条页面提取摘要"""
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return f"无法访问词条页面，状态码：{resp.status_code}"

            soup = BeautifulSoup(resp.text, 'lxml')

            # 方法1：尝试提取 meta description（通常包含摘要）
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                summary = meta_desc['content'].strip()
                return f"根据百度百科“{query}”词条：{summary}"

            # 方法2：提取 lemma-summary 节点（词条摘要）
            summary_div = soup.find('div', class_='lemma-summary')
            if summary_div:
                summary = summary_div.get_text(separator='', strip=True)
                if summary:
                    return f"根据百度百科“{query}”词条：{summary}"

            # 方法3：提取第一个段落
            first_para = soup.find('div', class_='para')
            if first_para:
                summary = first_para.get_text(strip=True)
                return f"根据百度百科“{query}”词条：{summary}"

            return f"找到词条“{query}”，但无法提取摘要。"

        except Exception as e:
            return f"提取词条内容时出错：{str(e)}"

    def run(self, query: str) -> str:
        """
        对外接口：根据查询返回百度百科摘要
        """
        return self._search_baike(query)


def generate_script(subject, video_length, creativity, api_key=None):
    """生成视频脚本（使用百度百科替代维基百科）"""

    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请提供 API Key 或设置环境变量 DASHSCOPE_API_KEY")

    # 标题生成模板
    title_template = ChatPromptTemplate.from_messages([
        ("human", "请为'{subject}'这个主题的视频想一个吸引人的标题")
    ])

    # 脚本生成模板（修正错别字）
    script_template = ChatPromptTemplate.from_messages([
        ("human",
         """你是一位短视频频道的博主。根据以下标题和相关信息，为短视频频道写一个视频脚本。
         视频标题：{title}，视频时长：{duration}分钟，生成的脚本的长度尽量遵循视频时长的要求。
         要求开头抓住眼球，中间提供干货内容，结尾有惊喜，脚本格式也请按照【开头、中间、结尾】分隔。
         整体内容的表达方式要尽量轻松有趣，吸引年轻人。
         脚本内容可以结合以下百度百科搜索出的信息，但仅作为参考，只结合相关的即可，对不相关的进行忽略：
         ```{baidu_search}```
         请用中文回答。""")
    ])

    # 初始化模型
    model = ChatTongyi(
        dashscope_api_key=api_key,
        model_name="qwen-plus",  # 可根据需要调整
        temperature=creativity
    )

    title_chain = title_template | model
    script_chain = script_template | model

    # 生成标题
    try:
        title = title_chain.invoke({"subject": subject}).content
    except Exception as e:
        raise RuntimeError(f"标题生成失败: {e}")

    # 百度百科搜索（增加异常处理和限流）
    baike = BaiduBaikeAPIWrapper(top_k_results=1)
    try:
        search_result = baike.run(subject)
        print(f"百度百科搜索完成，结果长度：{len(search_result)}")
    except Exception as e:
        print(f"⚠️ 百度百科搜索失败: {e}，将忽略外部信息")
        search_result = ""  # 置空，让模型自行发挥

    # 生成脚本
    try:
        script = script_chain.invoke({
            "title": title,
            "duration": video_length,
            "baidu_search": search_result
        }).content
    except Exception as e:
        raise RuntimeError(f"脚本生成失败: {e}")

    return search_result, title, script


# 测试代码
if __name__ == "__main__":
    # 假设环境变量 DASHSCOPE_API_KEY 已设置
    subject = "人工智能"
    wiki, title, script = generate_script(
        subject=subject,
        video_length=2,
        creativity=0.7
    )

    print("=" * 60)
    print("【百度百科参考】")
    print(wiki[:200] + "..." if len(wiki) > 200 else wiki)
    print("=" * 60)
    print("【生成的标题】")
    print(title)
    print("=" * 60)
    print("【生成的脚本】")
    print(script)
    print("=" * 60)