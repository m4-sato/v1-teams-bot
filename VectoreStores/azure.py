import os, traceback # 例外処理のトレース
import dotenv
dotenv.load_dotenv()

from langchain_openai import AzureOpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField
)
from langchain.schema import Document
from typing import List

#############################
# ベクターストアの立ち上げ設定
#############################

def azureLoad(fields=None):
    """
    fields:

    
    """
    # Azure AI Searchへベクトル登録するためのテキストエンベディングモデルを定義
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        openai_api_version="2023-05-15",
        model="text-embedding-ada-002",
        chunk_size=1
    )
    # Azure AI Searchのインスタンス設定
    vectore_store: AzureSearch = AzureSearch(
        azure_search_endpoint=os.environ['AZURE_VECTORE_STORES_ADDRESES'],
        azure_search_key=os.environ['AZURE_VECTORE_STORES_PASSWORD'],
        index_name=os.environ['AZURE_VECTORE_STORES_INDEX_NAME'],
        embedding_function=embeddings.embed_query,
        fields=fields
    )

    return vectore_store

#################################
# ベクターストアへのドキュメント追加
#################################

def azureAddDocuments(documents: list[Document]):
    # Azure向けの埋め込みクラスを生成
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],       # 旧: openai_api_base
        api_key=os.environ["AZURE_OPENAI_KEY"],             # 旧: openai_api_key
        openai_api_version="2023-05-15",       
        model="text-embedding-ada-002",
        chunk_size=1
        )

    # 使いたいモデルの埋め込み次元を実際に1回embedして調べる
    vector_search_dimensions = len(embeddings.embed_query("Text"))

    # ベクターストアでの検索フィールドの設定
    # metadataでフィルタリングする場合は、filterble=Trueを設定する。
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            Searchable=True,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            Searchable=True,
            vector_search_dimensions=vector_search_dimensions,
            vector_search_profile_name="myHnswProfile",
        ),
        SearchableField(
            name="metadata",
            type=SearchFieldDataType.String,
            searchable=True,
        )
        # SimpleField(
        #     name="notion_id", # フィルタリングしたいmetadataのキー
        #     type=SearchFieldDataType.String,# フィルタリングしたいmetadataの型
        #     filterable=True,# フィルタリングを可能にする。
        # ),
    ]

    # ベクターストアへのロード
    vectore_store = azureLoad(fields=fields)

    # ベクターストアへのドキュメント追加
    res = vectore_store.add_documents(documents)

    return res

################################
# ベクターストアへのベクトル検索
################################

def azureSearch(query, k:int=4, filters={}, search_type="hybrid") -> List[Document]:

    # ベクターストアのロード関数を呼ぶ ＆ ベクターストアからドキュメントを検索する。
    try:
        vectore_store = azureLoad()
        docs = vectore_store.similarity_search(query, k=k, filters=filters,search_type=search_type)
        return docs
    
    except Exception as e:
        return {"status": "ng", "error":traceback.format_exc()}