import os
import requests
import gradio as gr
from dotenv import load_dotenv
from gradio_pdf import PDF # PDF display from Gradio?

# Load environment variables
load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://rag:8000/ask/")
STATIC_PATH = os.getenv("STATIC_PATH", "/app/static/")
STATIC_ALLOWED_PATHS = [
    "/app/static/data/legal_english",
    "/app/static/data/legal_japanese",
    STATIC_PATH
]

# Chat function
def chat_with_bot(user_query, chat_history):
    payload = {"query_str": user_query}
    try:
        response = requests.post(FASTAPI_URL, json=payload)
        response.raise_for_status() 
        data = response.json()

        # Safely extract response data with fallback default
        answer = data.get("response", "")
        file_name = data.get("file_name", "N/A")
        page_label = data.get("page_label", "?")
        file_path = data.get("file_path", "")

        formatted_answer = (
            f"{answer}\n\n"
            f"**Source**: {file_name} (Page {page_label})"
        )

        chat_history.extend([
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": formatted_answer}
        ])

        # Ensure the file exists and is accessible
        if file_path and not os.path.isfile(file_path):
            file_path = None  # If the file doesn't exist, return None

        # Return chat history, blank string (for next input), and valid file path (if exists)
        return chat_history, "", file_path

    except requests.RequestException as err:
        error_msg = f"⚠️ Request error: {err}"
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"

    # Append the error message to chat history
    chat_history.extend([
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": error_msg}
    ])
    return chat_history, "", None

# UI Setup
with gr.Blocks(
    title="Glycine-AI",
    css="footer {visibility: hidden}",
    theme=gr.themes.Default(primary_hue="purple", secondary_hue="slate")
) as demo:

    gr.Markdown("# Glycine-AI - Legal AI solution for the Japanese financial market")
    gr.Markdown(
        "Built by [**Akim Mousterou**](https://www.linkedin.com/in/akim-mousterou/) during the "
        "***LLM x Law Hackathon #5*** at [**CodeX, Stanford Law School**]"
        "(https://law.stanford.edu/codex-the-stanford-center-for-legal-informatics/)"
    )
    gr.Markdown(
        "***Disclaimer***: *This tool is intended for informational and research purposes only. "
        "It utilizes publicly available content from Japan's [**FSA**](https://www.fsa.go.jp/en/index.html) "
        "and the [**SESC**](https://www.fsa.go.jp/sesc/english/index.html), including official English translations where available. "
        "Users are strongly advised to consult the original Japanese documents for accuracy and completeness. "
        "This tool does not provide legal, financial, or professional advice.* "
    )

    with gr.Tabs():
        with gr.TabItem("Chatbot"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbox = gr.Chatbot(label="Chatbot", type="messages", show_copy_button=True)
                    user_input = gr.Textbox(
                        placeholder="Ask about Japanese financial laws, regulations, and guidelines...",
                        submit_btn=True,
                        show_label=False,
                        lines=2,
                    )
                    gr.Examples(
                        examples=[
                            ["Give me the use cases of conventional AI in the financial sector observed by the FSA?"],
                            ["流動性カバレッジ比率を説明してください。"],
                            ["What are the strategic initiatives to promote Japan as a leading asset management center?"],
                            ["みずほ丸紅リース株式会社の本店等所在地は?"],
                        ],
                        inputs=user_input,
                        examples_per_page=4
                    )
                    state = gr.State([])

                with gr.Column(scale=2):
                    pdf_viewer = PDF(label="PDF preview")

            user_input.submit(
                fn=chat_with_bot,
                inputs=[user_input, state],
                outputs=[chatbox, user_input, pdf_viewer],
                show_progress="minimal"
            )

# Launch server
demo.launch(
    server_name=os.getenv("GRADIO_HOST", "0.0.0.0"),
    server_port=int(os.getenv("GRADIO_PORT", 7860)),
    share=False,
    favicon_path=os.path.join(STATIC_PATH, "qwen-wisteria.png"),
    allowed_paths=STATIC_ALLOWED_PATHS
)