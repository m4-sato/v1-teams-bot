import os
import dotenv
dotenv.load_dotenv()
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain_community.embeddings.openai import OpenAIEmbeddings
# from langchain_community.embeddings.azure_openai import AzureOpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField
)
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentanalysis import DocumentAnalysisClient

document_analysis_client = DocumentAnalysisClient(
    endpoint="YOUR_FORM_RECOGNIZER_ENDPOINT",
    credential=AzureKeyCredential("YOUR_FORM_RECOGNIZER_KEY")
)

with open("rouki_text.pdf", "rb") as f:
    poller = document_analysis_client.begin_analyze_document("prebuilt-document", f)
result = poller.result()

for i, page in enumerate(result.pages):
    text_lines = [line.content for line in page.lines]
    page_text = "\n".join(text_lines)
    print(f"--- page {i+1} ---")
    print(page_text)

# # 環境変数をロード
# load_dotenv()

loader = PyPDFLoader(
    # file_path = "./sample.pdf",
    file_path = "./rouki_text.pdf",
    extract_images = True
    )

document = loader.load()
print(document)


def txtToDocs(content:str, metadata:dict):
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
    splitted_docs = text_splitter.split_documents(docs)
    return splitted_docs


def azureLoad(fields=None):
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],       # 旧: openai_api_base
        api_key=os.environ["AZURE_OPENAI_KEY"],             # 旧: openai_api_key
        openai_api_version="2023-05-15",                           # バージョンを合わせる
        model="text-embedding-ada-002",
        chunk_size=1
    )
    # embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
    #     deployment=os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'],
    #     model_name=os.environ['AZURE_OPENAI_EMBEDDING_MODEL_NAME']
    # )
    
    vectore_store: AzureSearch = AzureSearch(
        azure_search_endpoint=os.environ['AZURE_VECTORE_STORES_ADDRESES'],
        azure_search_key=os.environ['AZURE_VECTORE_STORES_PASSWORD'],
        index_name=os.environ['AZURE_VECTORE_STORES_INDEX_NAME'],
        embedding_function=embeddings.embed_query,
        fields=fields
    )
    return vectore_store


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
            # Searchable=True,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            Searchable=True,
            vector_search_dimensions=vector_search_dimensions,
            # vector_search_configuration="default",
            vector_search_profile_name="myHnswProfile",
        ),
        SimpleField(
            name="metadata",
            type=SearchFieldDataType.String,
            filterable=False
        )
    ]

    vectore_store = azureLoad(fields=fields)
    res = vectore_store.add_documents(documents)
    return res

for doc in document:
    splitted_docs = txtToDocs(doc.page_content, doc.metadata)
    azureAddDocuments(splitted_docs)