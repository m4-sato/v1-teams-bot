const { ActivityHandler, MessageFactory, ActionTypes, CardFactory } = require('botbuilder');
const { CosmosClient } = require('@azure/cosmos');

const cosmosEndpoint = process.env.COSMOS_ENDPOINT;
const cosmosKey = process.env.COSMOS_KEY;
const databaseName = process.env.COSMOS_DB_DATABASE;
const containerName = process.env.COSMOS_DB_CONTAINER;
console.log('cosmosEndpoint=', cosmosEndpoint);
console.log('databaseName=', databaseName);
console.log('containerName=', containerName);

const OPENAI_RESOURCE = process.env.OPENAI_RESOURCE;
const OPENAI_DEPLOYMENT = process.env.OPENAI_DEPLOYMENT;
const OPENAI_API_VERSION = process.env.OPENAI_API_VERSION;
const OPENAI_COMPLETION_URL = `https://${OPENAI_RESOURCE}.openai.azure.com/openai/deployments/${OPENAI_DEPLOYMENT}/chat/completions?api-version=${OPENAI_API_VERSION}`;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const axios = require('axios');
const FASTAPI_CONVERSATION_ENDPOINT = 'http://127.0.0.1:8000/conversation_history';

var getCompletion = async function (text) {
    var data =  {
        messages:[
            {
                role: 'user', 
                content: text
            }
        ]
    };
    var res = await axios({
        method: 'post',
        url: OPENAI_COMPLETION_URL,
        headers: {
            'Content-Type': 'application/json',
            'api-key': OPENAI_API_KEY
        },
        data: data
    });
    return (res.data.choices[0] || []).message?.content;
};


class EchoBot extends ActivityHandler {
    constructor() {
        super();
        this.client = new CosmosClient({ endpoint: cosmosEndpoint, key: cosmosKey });
        this.database = this.client.database(databaseName);
        this.container = this.database.container(containerName);

        this.onMessage(async (context, next) => {
            await next();
            try {
                // === 1) ユーザーの入力をCosmos DBに保存 ===
                const userText = context.activity.text || '';
                const attachments = context.activity.attachments;
                const conversationId = context.activity.conversation.id; // ConversationIDを取得
                const userId = context.activity.from.id;                 // ユーザーIDなど

                if (attachments && attachments.length > 0) {
                    // 2) 添付ファイルがある場合は処理
                    for (const attachment of attachments) {
                        // 添付ファイルの情報
                        const { name, contentType, contentUrl } = attachment;
                        console.log("Attachment info:", name, contentType, contentUrl);
                
                        const userItemData = {
                            id: `${Date.now()}_user`,  // 適当なユニークID。Date.now()に_roleを付与するなど
                            conversationId: conversationId,
                            userId: userId,
                            role: "user",             // 役割を"user"として保存
                            message: userText,
                            timestamp: new Date().toISOString()
                        };
                        await this.container.items.create(userItemData);
                        console.log("User message stored in CosmosDB:", userItemData);
        
                        // ユーザーにエコーメッセージ(確認用)
                        await context.sendActivity(`Your message "${userText}" is stored in Cosmos DB!`);
                    }
                    
                } else {
                    const userItemData = {
                        id: `${Date.now()}_user`,  // 適当なユニークID。Date.now()に_roleを付与するなど
                        conversationId: conversationId,
                        userId: userId,
                        role: "user",             // 役割を"user"として保存
                        message: userText,
                        timestamp: new Date().toISOString()
                    };
                    await this.container.items.create(userItemData);
                    console.log("User message stored in CosmosDB:", userItemData);
    
                    // ユーザーにエコーメッセージ(確認用)
                    await context.sendActivity(`Your message "${userText}" is stored in Cosmos DB!`);

                    // === 2) FastAPIへ送信し、Bot応答を受け取る ===
                    const payload = { messages: [ { user: userText } ] };
                    const response = await axios.post(FASTAPI_CONVERSATION_ENDPOINT, payload);
                    console.log('FastAPIからのレスポンス', response.data);
            
                    if (response.data && response.data.bot) {
                        const botAnswer = response.data.bot;
                        const references = response.data.metadata;

                        // 参照情報をメッセージとして整形
                        let referenceMessage = '';
                        
                        if (Array.isArray(references) && references.length > 0) {
                            // 1) source+page+page_label 単位で重複排除
                            const uniqueRefsMap = new Map();
                            references.forEach((md) => {
                                const { source, page, page_label } = md;
                                // キーとなる文字列
                                const key = `${source}_${page}_${page_label}`;
                                uniqueRefsMap.set(key, { source, page, page_label });
                            });
                            const uniqueRefs = Array.from(uniqueRefsMap.values());

                            // 2) ユーザー向けにMarkdownテキストとして整形
                            referenceMessage = "\n\n---\n**参照情報**\n";
                            uniqueRefs.forEach((md, idx) => {
                                // 「(1) ファイル: sample.pdf, ページ: 3 (ラベル: 4)」のように表示
                                referenceMessage += `(${idx + 1}) ファイル: ${md.source}, ページ: ${md.page}`;
                                if (md.page_label) {
                                    referenceMessage += ` (ラベル: ${md.page_label})`;
                                }
                                referenceMessage += "\n";
                            });
                        }

                        // ユーザーにBot応答 + 参照情報を送る
                        // await context.sendActivity(`${botAnswer}${referenceMessage}`);
                        await context.sendActivity(botAnswer + referenceMessage);

                        // 2-1) 受け取ったBot応答をCosmos DBに保存
                        const botItemData = {
                            id: `${Date.now()}_bot`,
                            conversationId: conversationId,
                            userId: userId,
                            role: "assistant",        // 役割を"assistant"として保存
                            message: botAnswer,
                            timestamp: new Date().toISOString()
                        };
                        await this.container.items.create(botItemData);
                        console.log("Bot answer stored in CosmosDB:", botItemData);
            
                        // 2-2) ユーザーにBot応答を返す
                        await context.sendActivity(botAnswer);
            
                    } else if (response.data.error) {
                        await context.sendActivity('FastAPIでエラー: ' + response.data.error);
                    } else {
                        await context.sendActivity('FastAPIからのレスポンスを取得できませんでした。');
                    }
                }
            } catch (err) {
                console.error('Cosmos DB error:', err);
                await context.sendActivity('エラーが発生しました。');
            }
            
            await next();
        });

        this.onMembersAdded(async (context, next) => {
            const membersAdded = context.activity.membersAdded;
            const welcomeText = 'Hello and welcome!';
            for (let cnt = 0; cnt < membersAdded.length; ++cnt) {
                if (membersAdded[cnt].id !== context.activity.recipient.id) {
                    await context.sendActivity(MessageFactory.text(welcomeText, welcomeText));
                }
            }
            // By calling next() you ensure that the next BotHandler is run.
            await next();
        });
    }
}

module.exports.EchoBot = EchoBot;