const path = require('path');
// 🔥 保持 .env 配置
require('dotenv').config({ path: 'C:\\Users\\Administrator\\Desktop\\TaskLink\\.env' });

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');

const app = express();
const server = http.createServer(app);

const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'root',
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