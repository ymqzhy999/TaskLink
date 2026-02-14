const path = require('path');
// 🔥 保持 .env 配置
require('dotenv').config({ path: 'C:\\Users\\Administrator\\Desktop\\TaskLink\\.env' });

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');
const axios = require("axios");

const app = express();
const server = http.createServer(app);

// 2. 数据库连接池
const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'ymq20050704',
    database: process.env.DB_NAME || 'tasklink',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// 3. 配置中间件
app.use(cors());
app.use(express.json());

// 在线用户映射表
const onlineUsers = new Map();

// 4. 配置 Socket.IO
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// ==========================================
// 🔥🔥🔥 新闻核心业务 (GNews + Database) 🔥🔥🔥
// ==========================================

let newsCache = {
    data: null,
    lastFetch: 0
};

// 1. 获取每日新闻 (优先 API -> 存库 -> 失败则查库)
app.get('/api/news/daily', async (req, res) => {
    const NOW = Date.now();

    // A. 检查内存缓存 (1小时)
    if (newsCache.data && (NOW - newsCache.lastFetch < 3600000)) {
        console.log('📰 [NEWS] 使用内存缓存');
        return res.json({ code: 200, data: newsCache.data, source: 'cache' });
    }

    try {
        console.log('📰 [NEWS] 正在请求 GNews API...');

        // B. 请求 GNews API
        const response = await axios.get('https://gnews.io/api/v4/top-headlines', {
            params: {
                category: 'technology',
                lang: 'en',
                country: 'us',
                max: 10,
                apikey: process.env.GNEWS_API_KEY //
            },
            timeout: 15000
        });

        const rawArticles = response.data.articles || [];

        // C. 数据清洗
        const cleanArticles = rawArticles.map(item => ({
            title: item.title,
            description: item.description,
            url: item.url,
            image: item.image,
            source: item.source.name,
            publishedAt: item.publishedAt
        }));

        // D. 🔥 存入数据库 (使用 INSERT IGNORE 忽略重复 URL)
        if (cleanArticles.length > 0) {
            const connection = await pool.getConnection();
            try {
                await connection.beginTransaction();

                const sql = `INSERT IGNORE INTO news_articles 
                             (title, description, url, image_url, source_name, published_at, created_at) 
                             VALUES (?, ?, ?, ?, ?, ?, NOW())`;

                for (const article of cleanArticles) {
                    // 转换时间格式 ISO -> MySQL DateTime
                    const pubDate = new Date(article.publishedAt).toISOString().slice(0, 19).replace('T', ' ');

                    await connection.execute(sql, [
                        article.title,
                        article.description || '',
                        article.url,
                        article.image || '',
                        article.source,
                        pubDate
                    ]);
                }

                await connection.commit();
                console.log(`✅ [NEWS] ${cleanArticles.length} 条新闻处理完毕 (已存库/去重)`);
            } catch (err) {
                await connection.rollback();
                console.error('⚠️ [NEWS] 存库失败:', err);
            } finally {
                connection.release();
            }
        }

        // E. 更新缓存
        newsCache.data = cleanArticles;
        newsCache.lastFetch = NOW;

        res.json({ code: 200, data: cleanArticles, source: 'api' });

    } catch (error) {
        console.error('❌ [NEWS] API 获取失败:', error.message);

        // F. 降级策略：如果 API 挂了，从数据库捞最新的 10 条
        try {
            const [rows] = await pool.execute(
                'SELECT * FROM news_articles ORDER BY published_at DESC LIMIT 10'
            );

            // 格式化一下字段名以匹配前端
            const dbNews = rows.map(row => ({
                title: row.title,
                description: row.description,
                url: row.url,
                image: row.image_url,
                source: row.source_name,
                publishedAt: row.published_at
            }));

            console.log('🛡️ [NEWS] 已降级：返回数据库中的历史新闻');
            return res.json({ code: 200, data: dbNews, source: 'database_fallback' });

        } catch (dbError) {
            return res.status(500).json({ code: 500, msg: '新闻服务不可用' });
        }
    }
});

// 2. 获取历史新闻列表 (分页)
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


// ==========================================
// 🔥🔥🔥 Socket.IO 管理员踢人 & 聊天 🔥🔥🔥
// ==========================================

// 踢人接口
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

    // 监听：加入聊天
    socket.on('join', (userId) => {
        const uid = String(userId);
        onlineUsers.set(uid, socket.id);
        console.log(`👤 用户上线: ${uid} (Socket: ${socket.id})`);

        socket.join(`user_${uid}`);
        io.emit('update_online_count', onlineUsers.size);
    });

    // 监听：发送消息
    socket.on('send_message', async (data) => {
        const msgType = data.type || 'text';
        io.emit('new_message', {
            id: Date.now(),
            user_id: data.user_id,
            content: data.content,
            type: msgType,
            username: data.username,
            avatar: data.avatar,
            created_at: new Date()
        });
        try {
            const sql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
            await pool.execute(sql, [data.user_id, data.content, msgType]);
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
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