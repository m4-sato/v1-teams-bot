# v1-teams-bot

## 想定課題
- 膨大な文書データを検索し、何か判断を求める質問に答えることができるチャットボット(Microsoft Teams)

## ディレクトリ解説
- v1-teams-bot
  - my-chat-bot・・・Bot UIの役割を担っている。(Node.js)
  - server.py・・・文書の保存とベクトル検索するためのAPI(FastAPI)
  - utils.py・・・LangChainによる処理を定義（Text Splitter, Embedding, Chains, ChatHistory等）
  - VectoreStores・・・Azure AI Searchへの接続・文書を保存・文書検索に必要なコード
    - azure.py ・・・AzureサービスをPythonSDKにてコーディング(AzureOpenAI,　AzureAISearch, CosmosDB, LangChain等)

## 事前準備（Documentのベクトル化）
- ```merge.py```にpdfファイル（テキストベース）情報のファイルパスを指定する。
  本DEMOでは日本ディープラーニング協会が発行した生成AI利用ガイドラインの規則をチャンク＆ベクトル化＆インデクス化。

## サーバー起動

### Node.js
```bash
npm start
```

### FastAPI
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 参考文献
- [LangChain](https://www.langchain.com/)
- [microsoft azure generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners)