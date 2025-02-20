import os
import dotenv
dotenv.load_dotenv()
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores.azuresearch import AzureSearch

#################################################
# 文章とメタデータを受け取り、Documentのリストを返す
#################################################


def txtToDocs(content:str, metadata:dict):
    # ドキュメントのリストを作成
    docs = [Document(page_content=content, metadata=metadata)]
    chunk_size =300
    separator="\n"
    chunk_overlap=100
    text_splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
        )
    
    # ドキュメントのリストを設定したパラメータで分割
    splitted_docs = text_splitter.split_documents(docs)
    return splitted_docs

######################
# チャットボットの実行
######################

def chatExecute(
        query:str,# ユーザーの質問
        vectore_store: AzureSearch,
        chat_history:list[tuple]=[],
        search_type="similarity",
        search_kwards={}
        ):
    
    # ベクターストアから検索結果を取得するためのインスタンスを作成
    retriver = vectore_store.as_retriever(
        search_type=search_type,
        search_kwards=search_kwards
    )

    # LLMのインスタンスを作成
    chat = AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-05-01-preview",
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        temperature=0
        )
    
    # チャットボットのインスタンスを作成
    qa = ConversationalRetrievalChain.from_llm(
        llm=chat,
        retriever = retriver,
        return_source_documents=True,
        chain_type="stuff"
        )
    
    # チャットボットの実行
    result = qa({'question': query, "chat_history": chat_history})
    # チャットボットの回答
    answer = result['answer']
    # チャットボットの回答に対応するメタデータのリスト
    metadatas = [doc.metadata for doc in result['source_documents']]
    # 会話履歴に追加
    chat_history.append((query, result['answer']))
    return (answer, chat_history, metadatas)

###########################
# chat_historyをリストに変換
###########################

def chatHistoryToList(chat_history:list[dict]) -> list[tuple]:
    chat_history_list = []
    skip = False
    for i, chat in enumerate(chat_history):
        if skip:
            skip = False
            continue
        if "user" in chat:
            if i+1 <len(chat_history):
                if "bot" in chat_history[i+1]:
                    chat_history_list.append((chat["user"], chat_history[i+1]["bot"]))
                    skip=True
                else:
                    chat_history_list.append((chat["user"], ""))
                    skip = False
            else:
                chat_history_list.append((chat["user"], ""))
                skip = False

    return chat_history_list