# v1-teams-bot

## ディレクトリ解説
- v1-teams-bot
  - my-chat-bot
  - server.py・・・文書の保存とベクトル検索するためのAPI化
  - VectoreStores・・・Azure AI Searchへの接続・文書を保存・文書検索に必要なコード
    - azure.py 

## Documentのベクトル化
- ```merge.py```にpdfファイル（テキストベース）情報のファイルパスを指定する。


## FastAPI
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
