import os
import dotenv
dotenv.load_dotenv()
from fastapi import FastAPI
from utils import txtToDocs, chatExecute, chatHistoryToList
from VectoreStores.azure import azureAddDocuments, azureSearch, azureLoad
import traceback

app = FastAPI()


@app.post("/add_document", description="ベクターストアへのドキュメント追加")
def add_document(parameters: dict):
    content = parameters["content"]
    metadata = parameters["metadata"]
    docs = txtToDocs(content, metadata)
    return azureAddDocuments(documents=docs)


@app.post("/doc_search", description="ベクターストアへのベクトル検索")
def search(parameters: dict):
    # 検索クエリ
    query = parameters["query"]

    # 取得するドキュメント数
    if "doc_num" in parameters:
        k = int(parameters["doc_num"])
    # else:
    #     k = os.environ['DOCUMENT_NUM']
    
    filters = {}

    # フィルタリングするmetadataの取得
    if "filters" in parameters:
        filters = parameters["filters"]
    else:
        filters = None

    # 検索タイプの取得("similarity", "hybrid", "semantic_hybrid"のいずれか)
    search_type = "hybrid"
    if "search_type" in parameters:
        search_type = parameters["search_type"]
    
    return azureSearch(query=query, k=k, filters=filters, search_type=search_type)


@app.post("/conversation_history", description="会話履歴")
async def add_bot_message(conversation_history: dict):
    try:
        chat_history = conversation_history["messages"]

        if len(chat_history) == 0:
            return {"bot": "チャット履歴が空です", "metadata": {}}
        
        if "bot" in chat_history[-1]:
            return {"bot": "チャット履歴の末尾はユーザーの質問である必要があります。", "metadata": {}}
        
        query = chat_history[-1]["user"]

        if len(chat_history) > 0:
            chat_history.pop(-1)
            chat_history = chatHistoryToList(chat_history)

        
        search_kwards = {}

        if "filters" in conversation_history:
            filters = conversation_history["filters"]
            search_kwards["filters"] = filters
        
        if "doc_num" in conversation_history:
            search_kwards['k'] = conversation_history['doc_num']
        # else:
        #     search_kwards['k'] = os.environ['DOCUMENT_NUM']
        
        if 'search_type' in conversation_history:
            search_kwards['search_type'] = conversation_history['search_type']
        else:
            search_kwards['search_type'] = 'hybrid'
        
        (answer, res_chat_history, res_metadata) = chatExecute(
            query, 
            vectore_store=azureLoad(),
            search_kwards=search_kwards,
            chat_history=chat_history
        )

        return {"bot": answer, "metadata": res_metadata}
    
    except Exception as e:
        return {"error": traceback.format_exc()}