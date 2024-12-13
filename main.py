import streamlit
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part, Tool
from vertexai.preview import generative_models as preview_generative_models

import streamlit_authenticator
import yaml
from yaml.loader import SafeLoader

# 環境変数の設定
PROJECT_ID = "{プロジェクトID}"  # Google Cloud プロジェクトの ID
LOCATION = "{リージョン}"  # Gemini モデルを使用するリージョン

START_PROMPTS = """あなたは日本の小売業の店員です。
お客様からの質問に対して、以下の「キャラクターシート」に従ってお客様に商品を提案してください。

## 小売業の店員のキャラクターシート:
- 外見
    - 丁寧で落ち着いた話し方
- 人柄
    - 親切で丁寧
"""


# Vertex AI API の初期化
vertexai.init(project=PROJECT_ID, location=LOCATION)

# ユーザー設定読み込み
yaml_path = "./config.yaml"

with open(yaml_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# タイトルを設定する
streamlit.set_page_config(
    page_title="Chat app with Gemini",
    page_icon="🤖",
    initial_sidebar_state="collapsed",
)

streamlit.title("Chat app with Gemini")

authenticator = streamlit_authenticator.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    cookie_key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"],
)

authenticator.login()

def create_model(select_model, generation_config, select_grounding, input_datastore):
    if select_grounding == "Vertex AI Search":
        vertex_search_tool = Tool.from_retrieval(
            retrieval=preview_generative_models.grounding.Retrieval(
                source=preview_generative_models.grounding.VertexAISearch(
                    datastore=input_datastore
                ),
            )
        )
        tools = [vertex_search_tool]
    elif select_grounding == "Google検索":
        vertex_search_tool = Tool.from_google_search_retrieval(
            google_search_retrieval=preview_generative_models.grounding.GoogleSearchRetrieval()
        )
        tools = [vertex_search_tool]
    else:
        tools = []
    return GenerativeModel(
        model_name=select_model,
        generation_config=generation_config,
        tools=tools,
        system_instruction=[str(input_prompt)],
    )

if streamlit.session_state["authentication_status"]:
    with streamlit.sidebar:
        streamlit.markdown(f'## Welcome *{streamlit.session_state["name"]}*')
        authenticator.logout("Logout", "sidebar")
        streamlit.divider()

        # 使えるモデル情報：https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models
        select_model = streamlit.selectbox(
            "Model",
            [
                "gemini-1.5-flash-002",
                "gemini-1.5-pro",
            ],
        )
        select_temperature = streamlit.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.1,
        )
        select_top_p = streamlit.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.01,
        )  # 生成するテキストのランダム性を制御
        select_output_tokens = streamlit.slider(
            "Max Output Tokens",
            min_value=0,
            max_value=4096,
            value=2048,
            step=512,
        )  # 最大出力トークン数を指定
        input_prompt = (
            streamlit.text_area(
                label="prompt", value=START_PROMPTS, height=300, max_chars=2048
            ),
        )
        select_grounding = streamlit.radio(
            label="Grounding",
            options=["Vertex AI Search", "Google検索", "なし"],
            horizontal=True,
        )
        input_datastore = streamlit.text_input(
            label="Vertex AI Search Datastore",
            placeholder="Paste datastore path",
            value="projects/{プロジェクトID}/locations/global/collections/default_collection/dataStores/{データストアID}",
        )

    # 設定を反映する用のボタンをsidebarに設置する
    if streamlit.sidebar.button("Apply"):
        streamlit.session_state.pop("chat_session", None)
        streamlit.session_state.pop("chat_history", None)

    # セッション状態の初期化
    if "chat_session" not in streamlit.session_state:
        # llmモデルのconfig
        generation_config = {
            "temperature": select_temperature,
            "top_p": select_top_p,
            "max_output_tokens": select_output_tokens,
        }

        model = create_model(select_model, generation_config, select_grounding, input_datastore)

        streamlit.session_state["chat_session"] = model.start_chat(
            history=[
                # 何か開始前の初期やりとりをさせる場合は追加
                # Content(role="user", parts=[Part.from_text(text="あなたは優秀なAIアシスタントです。できるだけ簡潔に回答してください。")]),
                # Content(role="model", parts=[Part.from_text(text="わかりました。")])
            ]
        )
        streamlit.session_state["chat_history"] = []

    # チャット履歴を全て表示
    for message in streamlit.session_state["chat_history"]:
        with streamlit.chat_message(message["role"]):
            streamlit.markdown(message["content"])

    # ユーザー入力送信後処理
    if prompt := streamlit.chat_input("ここに入力してください"):

        # ユーザの入力を表示する
        with streamlit.chat_message("user"):
            streamlit.markdown(prompt)

        # ユーザの入力をチャット履歴に追加する
        streamlit.session_state["chat_history"].append(
            {"role": "user", "content": prompt}
        )

        # Genimi Proにメッセージ送信
        response = streamlit.session_state["chat_session"].send_message(prompt)

        # Genimi Proのレスポンス表示
        with streamlit.chat_message("assistant"):
            streamlit.markdown(response.text)

        # Genimi Proのレスポンスをチャット履歴に追加する
        streamlit.session_state["chat_history"].append(
            {"role": "assistant", "content": response.text}
        )


elif streamlit.session_state["authentication_status"] is False:
    ## ログイン成功ログイン失敗
    streamlit.error("Username/password is incorrect")

elif streamlit.session_state["authentication_status"] is None:
    ## デフォルト
    streamlit.warning("Please enter your username and password")
