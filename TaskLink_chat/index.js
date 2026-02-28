const path = require('path');
require('dotenv').config({ path: 'C:\\Users\\Administrator\\Desktop\\TaskLink\\.env' });

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');
const fs = require('fs');
const Redis = require('ioredis');

// Flask API 地址
const FLASK_API = process.env.FLASK_API || 'http://101.35.132.175:5000';

// ==================== Redis 配置 ====================
const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = process.env.REDIS_PORT || 6379;
const REDIS_PASSWORD = process.env.REDIS_PASSWORD || null;
const CHAT_CACHE_TTL = 300;

// 创建 Redis 客户端
let redisClient = null;
try {
    redisClient = new Redis({
        host: REDIS_HOST,
        port: REDIS_PORT,
        password: REDIS_PASSWORD,
        retryDelayOnFailover: 100,
        maxRetriesPerRequest: 3,
        lazyConnect: true
    });
    
    redisClient.on('connect', () => {
        console.log(`✅ Redis 连接成功: ${REDIS_HOST}:${REDIS_PORT}`);
    });
    
    redisClient.on('error', (err) => {
        console.log(`⚠️ Redis 连接失败: ${err.message}`);
    });
    
    // 尝试连接
    redisClient.connect().catch(err => {
        console.log(`⚠️ Redis 自动连接跳过: ${err.message}`);
    });
} catch (err) {
    console.log(`⚠️ Redis 初始化失败: ${err.message}`);
}

// 缓存 Key 生成函数
function getChatCacheKey(offset, limit) {
    return `chat:messages:${offset}:${limit}`;
}

// 写入消息到 Redis 缓存
async function cacheChatMessages(offset, limit, messages) {
    if (!redisClient || redisClient.status !== 'ready') {
        return false;
    }
    
    try {
        const key = getChatCacheKey(offset, limit);
        await redisClient.setex(key, CHAT_CACHE_TTL, JSON.stringify(messages));
        console.log(`💾 [Redis] 缓存消息 offset=${offset}, count=${messages.length}`);
        return true;
    } catch (err) {
        console.log(`⚠️ [Redis] 缓存写入失败: ${err.message}`);
        return false;
    }
}

// 清除聊天缓存
async function clearChatCache() {
    if (!redisClient || redisClient.status !== 'ready') {
        return;
    }
    
    try {
        const keys = await redisClient.keys('chat:messages:*');
        if (keys.length > 0) {
            await redisClient.del(...keys);
            console.log(`🗑️ [Redis] 清除 ${keys.length} 个缓存键`);
        }
    } catch (err) {
        console.log(`⚠️ [Redis] 清除缓存失败: ${err.message}`);
    }
}

// 将新消息同步到 Redis 缓存
async function syncNewMessageToRedis(newMsg) {
    if (!redisClient || redisClient.status !== 'ready') {
        return;
    }
    
    try {
        // 1. 更新最新消息缓存 (offset=0, limit=50)
        const latestKey = getChatCacheKey(0, 50);
        let latestCache = await redisClient.get(latestKey);
        
        let messages = [];
        if (latestCache) {
            messages = JSON.parse(latestCache);
        }
        
        // 将新消息添加到数组末尾（最新的在最后）
        messages.push(newMsg);
        
        // 保持最多 50 条最新消息
        if (messages.length > 50) {
            messages = messages.slice(-50);
        }
        
        // 写回 Redis
        await redisClient.setex(latestKey, CHAT_CACHE_TTL, JSON.stringify(messages));
        console.log(`💾 [Redis] 同步新消息到缓存，当前缓存 ${messages.length} 条`);
        
    } catch (err) {
        console.log(`⚠️ [Redis] 同步新消息失败: ${err.message}`);
    }
}

const app = express();
const server = http.createServer(app);

// DeepSeek 配置
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;
const DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions';
const MEMORY_FILE = path.join(__dirname, 'memory.md');
const CONVERSATION_FILE = path.join(__dirname, 'conversation_history.md');

// 读取提示词文件
function getSystemPrompt() {
    try {
        if (fs.existsSync(MEMORY_FILE)) {
            return fs.readFileSync(MEMORY_FILE, 'utf-8');
        }
    } catch (e) {
        console.error('❌ 读取 memory.md 失败:', e);
    }
    return '你是一个友好的AI助手名叫波比。';
}

// 读取对话历史
function getConversationHistory() {
    try {
        if (fs.existsSync(CONVERSATION_FILE)) {
            return fs.readFileSync(CONVERSATION_FILE, 'utf-8');
        }
    } catch (e) {
        console.error('❌ 读取对话历史失败:', e);
    }
    return '';
}

// 保存对话到历史记录
function saveConversation(userQuestion, botAnswer, username) {
    try {
        let history = getConversationHistory();
        const timestamp = new Date().toLocaleString('zh-CN');
        const newEntry = `\n\n## ${timestamp} - 用户: ${username}\n**用户**: ${userQuestion}\n\n**波比**: ${botAnswer}\n`;
        
        fs.writeFileSync(CONVERSATION_FILE, history + newEntry, 'utf-8');
        console.log('💾 对话已保存到历史记录');
    } catch (e) {
        console.error('❌ 保存对话失败:', e);
    }
}

// 调用 DeepSeek Chat API
async function callDeepSeekChat(userQuestion, username) {
    const systemPrompt = getSystemPrompt();
    const conversationHistory = getConversationHistory();
    
    // 构建消息列表
    const messages = [
        { role: 'system', content: systemPrompt }
    ];
    
    // 添加历史对话（如果太长则截断）
    if (conversationHistory) {
        const historyContent = `以下是之前的对话历史供参考：\n${conversationHistory}`;
        // 限制历史长度，避免超过 token 限制
        const truncatedHistory = historyContent.length > 2000 ? 
            historyContent.slice(-2000) : historyContent;
        messages.push({ role: 'system', content: truncatedHistory });
    }
    
    // 添加当前用户问题，并说明是谁在提问
    messages.push({ role: 'user', content: `【当前对话】用户 "${username}" 对你说：${userQuestion}\n\n请用友好的方式回答，并正确称呼这位用户的名字"${username}"。` });
    
    try {
        const response = await fetch(DEEPSEEK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
            },
            body: JSON.stringify({
                model: 'deepseek-chat',
                messages: messages,
                temperature: 0.5,  // 降低温度，让回答更稳定、更像真人
                top_p: 0.9,       // 配合 temperature 使用
                max_tokens: 1000
            })
        });
        
        const data = await response.json();
        
        if (data.choices && data.choices[0]) {
            return data.choices[0].message.content;
        } else {
            console.error('❌ DeepSeek API 返回异常:', data);
            return '抱歉，我现在有点困惑，请稍后再试~';
        }
    } catch (e) {
        console.error('❌ 调用 DeepSeek 失败:', e);
        return '抱歉，连接出了问题，请稍后再试~';
    }
}

const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'ymq20050704',
    database: process.env.DB_NAME || 'tasklink',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

app.use(cors());
app.use(express.json());

const onlineUsers = new Map();

const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

app.get('/api/news/history', async (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const pageSize = parseInt(req.query.pageSize) || 20;
    const offset = (page - 1) * pageSize;

    try {
        const [rows] = await pool.execute(
            'SELECT * FROM news_articles ORDER BY published_at DESC LIMIT ? OFFSET ?',
            [String(pageSize), String(offset)] // MySQL limit 需要字符串或数字，但在 execute 中有时要注意类型
        );

        res.json({ code: 200, data: rows });
    } catch (error) {
        console.error(error);
        res.status(500).json({ code: 500, msg: '查询失败' });
    }
});

app.post('/kick', async (req, res) => {
    const { user_id } = req.body;
    const uid = String(user_id);
    console.log(`🔨 [KICK] 收到指令，准备清理用户: ${uid}`);

    const roomName = `user_${uid}`;
    io.to(roomName).emit('force_logout', { msg: '您的账号已被管理员禁用' });

    setTimeout(async () => {
        try {
            await io.in(roomName).disconnectSockets(true);
            onlineUsers.delete(uid);
            io.emit('update_online_count', onlineUsers.size);
            console.log(`✅ [KICK] 用户 ${uid} 已被连根拔起`);
        } catch (e) {
            console.error(`❌ [KICK] 断开连接失败:`, e);
        }
    }, 100);

    return res.json({ code: 200, msg: '踢出指令已执行' });
});

io.on('connection', (socket) => {
    console.log('🟢 新连接接入:', socket.id);

    socket.on('join', (userId) => {
        const uid = String(userId);
        onlineUsers.set(uid, socket.id);
        console.log(`👤 用户上线: ${uid} (Socket: ${socket.id})`);

        socket.join(`user_${uid}`);
        io.emit('update_online_count', onlineUsers.size);
    });

    socket.on('send_message', async (data) => {
        const msgType = data.type || 'text';
        const content = data.content || '';
        
        // 先发送用户消息
        io.emit('new_message', {
            id: Date.now(),
            user_id: data.user_id,
            content: content,
            type: msgType,
            username: data.username,
            avatar: data.avatar,
            created_at: new Date().toISOString()
        });
        
        // 保存到数据库
        try {
            const sql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
            const userId = parseInt(data.user_id) || 0;
            const [result] = await pool.query(sql, [userId, content, msgType]);
            const insertId = result.insertId;
            
            // 获取新插入的消息详情
            const [msgRows] = await pool.query(
                'SELECT * FROM chat_messages WHERE id = ?',
                [insertId]
            );
            
            if (msgRows.length > 0) {
                const newMsg = msgRows[0];
                const msgObj = {
                    id: newMsg.id,
                    user_id: newMsg.user_id,
                    content: newMsg.content,
                    type: newMsg.msg_type,
                    username: data.username || '用户',
                    avatar: data.avatar || '',
                    created_at: newMsg.created_at,
                    is_bot: false
                };
                
                // 自动同步到 Redis 缓存（更新最新消息）
                await syncNewMessageToRedis(msgObj);
            }
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
        }
        
        // ===== 波比机器人检测 =====
        if (content.includes('@波比') || content.includes('@波比 ')) {
            console.log(`🤖 [波比] 检测到用户@，准备回复: ${data.username}`);
            
            // 提取问题（去掉 @波比）
            let question = content.replace(/@波比[，,]?\s*/g, '').trim();
            
            // 如果去掉 @波比 后为空，说明只是 @了一下，给个友好提示
            if (!question) {
                question = '你好呀！';
            }
            
            // 显示"正在输入"状态（可选）
            io.emit('bot_typing', { bot: '波比', isTyping: true });
            
            try {
                // 调用 DeepSeek 获取回复
                const botReply = await callDeepSeekChat(question, data.username);
                
                // 发送波比的回复
                io.emit('new_message', {
                    id: Date.now(),
                    user_id: 0, // 0 表示系统/机器人
                    content: botReply,
                    type: 'text',
                    username: '波比',
                    avatar: './bot.jpg',
                    created_at: new Date().toISOString(),
                    is_bot: true // 标记为机器人消息
                });
                
                // 保存波比消息到数据库 (user_id=21 是波比的账号)
                try {
                    const botSql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
                    const [result] = await pool.query(botSql, [21, botReply, 'text']);
                    
                    // 获取波比消息详情并同步到 Redis
                    const [botRows] = await pool.query('SELECT * FROM chat_messages WHERE id = ?', [result.insertId]);
                    if (botRows.length > 0) {
                        const botMsg = {
                            id: botRows[0].id,
                            user_id: botRows[0].user_id,
                            content: botRows[0].content,
                            type: botRows[0].msg_type,
                            username: '波比',
                            avatar: './bot.jpg',
                            created_at: botRows[0].created_at,
                            is_bot: true
                        };
                        await syncNewMessageToRedis(botMsg);
                    }
                } catch (err) {
                    console.error('❌ 波比消息存库失败:', err);
                }
                
                // 保存对话到历史
                saveConversation(question, botReply, data.username);
                
                console.log(`✅ [波比] 回复已发送`);
            } catch (e) {
                console.error('❌ [波比] 回复失败:', e);
                io.emit('new_message', {
                    id: Date.now(),
                    user_id: 0,
                    content: '抱歉，我刚才走神了，请稍后再试~',
                    type: 'text',
                    username: '波比',
                    avatar: './bot.jpg',
                    created_at: new Date().toISOString(),
                    is_bot: true
                });
                
                // 错误消息也保存到数据库
                try {
                    const botSql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
                    await pool.query(botSql, [21, '抱歉，我刚才走神了，请稍后再试~', 'text']);
                } catch (err) {
                    console.error('❌ 波比错误消息存库失败:', err);
                }
            }
            
            // 取消"正在输入"状态
            io.emit('bot_typing', { bot: '波比', isTyping: false });
        }
    });

    socket.on('disconnect', () => {
        let disconnectedUser = null;
        for (const [uid, sid] of onlineUsers.entries()) {
            if (sid === socket.id) {
                onlineUsers.delete(uid);
                disconnectedUser = uid;
                break;
            }
        }
        if (disconnectedUser) {
            console.log(`🔴 用户离线: ${disconnectedUser}`);
        }
        io.emit('update_online_count', onlineUsers.size);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🚀 服务运行在: http://localhost:${PORT}`);
});