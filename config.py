import os
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from dotenv import load_dotenv

load_dotenv()

# English Prompt Functions
def english_completion_to_prompt(completion):
    return (
        "<|im_start|>system\n<|im_end|>\n"
        f"<|im_start|>user\n{completion}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

def english_messages_to_prompt(messages):
    prompt = ""
    for message in messages:
        if message.role == "system":
            prompt += f"<|im_start|>system\n{message.content}<|im_end|>\n"
        elif message.role == "user":
            prompt += f"<|im_start|>user\n{message.content}<|im_end|>\n"
        elif message.role == "assistant":
            prompt += f"<|im_start|>assistant\n{message.content}<|im_end|>\n"
    if not prompt.startswith("<|im_start|>system"):
        prompt = (
            "<|im_start|>system\nYou are an intelligent assistant for legal documents. "
            "Your task is to provide accurate answers based solely on the given context and the user's question.<|im_end|>\n"
            + prompt
        )
    return prompt + "<|im_start|>assistant\n"

# Japanese Prompt Functions
def japanese_completion_to_prompt(completion):
    return (
        "<|im_start|>system\n<|im_end|>\n"
        f"<|im_start|>user\n{completion}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

def japanese_messages_to_prompt(messages):
    prompt = ""
    for message in messages:
        if message.role == "system":
            prompt += f"<|im_start|>system\n{message.content}<|im_end|>\n"
        elif message.role == "user":
            prompt += f"<|im_start|>user\n{message.content}<|im_end|>\n"
        elif message.role == "assistant":
            prompt += f"<|im_start|>assistant\n{message.content}<|im_end|>\n"
    if not prompt.startswith("<|im_start|>system"):
        prompt = (
            "<|im_start|>system\nあなたは法令関連文書に関するインテリジェント・アシスタントです。"
            "与えられたコンテキストとユーザーの質問のみに基づいて、正確な回答を提供してください。<|im_end|>\n"
            + prompt
        )
    return prompt + "<|im_start|>assistant\n"

# Setup Model and Embeddings
def setup_model_and_embeddings(language: str):
    from llama_index.llms.ollama import Ollama

    # Choose prompt formatting based on language
    completion_to_prompt = japanese_completion_to_prompt if language == "ja" else english_completion_to_prompt
    messages_to_prompt = japanese_messages_to_prompt if language == "ja" else english_messages_to_prompt

    # Setup LLM and Embedding Model
    Settings.llm = Ollama(
        model="qwen2.5:3b-instruct",
        request_timeout=500,
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
        temperature=0.1,
        top_k=6,
        top_p=0.7,
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        options={"num_gpu": 0}
    )

    # Set the embed model path
    embed_model = os.getenv('EMBED_MODEL', '/app/embed_model')

    # Ensure the model path exists before setting the embedding model
    if not os.path.exists(embed_model):
        print(f"Embedding model path does not exist: {embed_model}")
        return

    Settings.embed_model = HuggingFaceEmbedding(embed_model)
    Settings.text_splitter = SentenceSplitter(chunk_size=1024)

def get_static_folder_path(language: str):
    if language == "ja":
        return "/app/static/data/legal_japanese"
    else:
        return "/app/static/data/legal_english"