# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import SpacyTextSplitter
import os
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter


# 環境変数をロード
load_dotenv()

loader = PyPDFLoader(
    file_path = "./sample.pdf",
    extract_images = True
    )

document = loader.load()
print(document)

def txtToDocs(content:str, metadata:dict):
    docs = [Document(page_content=docs, metadata=metadata)]
    chunk_size =300,
    separator="\n",
    chunk_overlap=100,
    text_splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
        )
    splitted_docs = text_splitter.split_documents(docs)
    return splitted_docs

