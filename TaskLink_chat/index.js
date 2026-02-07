// TaskLink_chat/index.js
require('dotenv').config(); // 读取 .env

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');

// --- 1. 初始化应用 ---
const app = express();
const server = http.createServer(app);


const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'root', // 这里填你的数据库密码
    database: process.env.DB_NAME || 'tasklink',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// --- 3. 配置中间件 ---
app.use(cors()); // 允许跨域
app.use(express.json());

// --- 4. 配置 Socket.IO ---
const io = new Server(server, {
    cors: {
        origin: "*", // 允许任何前端连接（生产环境建议限制 IP）
        methods: ["GET", "POST"]
    }
});

// --- 5. Socket.IO 核心业务 ---
io.on('connection', (socket) => {
    console.log('🟢 新用户连接:', socket.id);

    // 监听：加入聊天
    socket.on('join', (userId) => {
        socket.join(`user_${userId}`);
        console.log(`用户 ${userId} 已上线`);
    });

    // 监听：发送消息
    socket.on('send_message', async (data) => {
        // data: { user_id, content, type }
        console.log(`收到消息:`, data);

        // A. 广播给所有人
        io.emit('new_message', {
            id: Date.now(), // 临时 ID
            user_id: data.user_id,
            content: data.content,
            created_at: new Date()
        });

        // B. 异步存入数据库 (不阻塞聊天)
        try {
            const [result] = await pool.execute(
                'INSERT INTO chat_messages (user_id, content, msg_type) VALUES (?, ?, ?)',
                [data.user_id, data.content, 'text']
            );
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
        }
    });

    socket.on('disconnect', () => {
        console.log('🔴 用户断开:', socket.id);
    });
});

// --- 6. 基础 API 测试接口 ---
app.get('/', (req, res) => {
    res.send('TaskLink Chat Server is Running...');
});

// --- 7. 启动服务器 ---
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🚀 聊天服务器运行在: http://localhost:${PORT}`);
});