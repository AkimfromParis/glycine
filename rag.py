import textwrap
from langdetect import detect
from config import setup_model_and_embeddings, get_static_folder_path
from query_engine import create_query_engine
from llama_index.core.prompts import RichPromptTemplate

english_prompt_tmpl_str = """
You are an intelligent assistant for legal documents. Your task is to provide accurate answers based solely on the given context and the user's question.

context:
{{ context_str }}

user's question:
{{ query_str }}

Instructions:
    - Provide a clear response based only on the context without any additional commentary, search options, advice, follow-up questions, or alternative ideas.
    - Do NOT include emojis, backlinks, URLs, hashtags, or any other supplementary information.
    - Avoid repeating the same sentence or phrase multiple times.

Answer:
"""

japanese_prompt_tmpl_str = """
あなたは法令関連文書に関するインテリジェント・アシスタントです。与えられたコンテキストとユーザーの質問のみに基づいて、正確な回答を提供してください。

コンテキスト:
{{ context_str }}

ユーザーの質問:
{{ query_str }}

指示:
    - コンテキストのみに基づいて明確に回答してください。コメント、検索オプション、助言、追加の質問、代替案などは含めないでください。
    - 絵文字、バックリンク、URL、ハッシュタグ、その他の補足情報は含めないでください。
    - 同じ文やフレーズを繰り返さないでください。

回答:
"""

def detect_language(text: str):
    """Detect the language of the provided text."""
    try:
        return detect(text)
    except:
        return "en"

def process_query(query_str: str):
    from typing import Any

    def safe_get(metadata: dict, key: str, default: Any = "N/A"):
        value = metadata.get(key, default)
        return value if isinstance(value, (str, int, float)) else str(value)

    language = detect_language(query_str)

    prompt_tmpl = RichPromptTemplate(
        japanese_prompt_tmpl_str if language == "ja" else english_prompt_tmpl_str
    )
    setup_model_and_embeddings(language)
    folder_path = get_static_folder_path(language)
    hybrid_query_engine = create_query_engine(language, prompt_tmpl)

    response_obj = hybrid_query_engine.query(query_str)

    answer = response_obj.response

    source_nodes = response_obj.source_nodes
    if source_nodes:
        node_info = source_nodes[0].node.extra_info
        page_label = safe_get(node_info, "page_label")
        file_name = safe_get(node_info, "file_name")
        file_path = safe_get(node_info, "file_path")
    else:
        page_label = file_name = file_path = "N/A"

    return {
        "response": answer.strip(),
        "page_label": page_label,
        "file_name": file_name,
        "file_path": file_path
    }