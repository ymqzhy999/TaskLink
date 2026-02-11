require('dotenv').config();

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');

// --- 1. 初始化应用 ---
const app = express();
const server = http.createServer(app);

// --- 2. 数据库连接池 ---
const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'root',
    database: process.env.DB_NAME || 'tasklink',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// --- 3. 配置中间件 ---
app.use(cors());
app.use(express.json());

// 在线用户映射表
const onlineUsers = new Map();

// --- 4. 配置 Socket.IO (先定义 io 变量！) ---
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// --- 🔥🔥🔥 5. 踢人接口 (必须放在 io 定义之后) 🔥🔥🔥 ---
app.post('/kick', async (req, res) => {
    const { user_id } = req.body;
    const uid = String(user_id);

    console.log(`🔨 [KICK] 收到指令，准备清理用户: ${uid}`);

    // 1. 获取该用户房间内的所有 Socket
    const roomName = `user_${uid}`;

    // 2. 先向该房间广播“强制下线”事件
    io.to(roomName).emit('force_logout', { msg: '您的账号已被管理员禁用' });

    // 3. 稍等 100毫秒，确保客户端收到消息后再断开
    setTimeout(async () => {
        try {
            // 🔥 核心绝杀：强制断开该房间下的所有连接
            await io.in(roomName).disconnectSockets(true);

            // 4. 清理内存 Map
            onlineUsers.delete(uid);

            // 5. 更新在线人数
            io.emit('update_online_count', onlineUsers.size);

            console.log(`✅ [KICK] 用户 ${uid} 已被连根拔起`);
        } catch (e) {
            console.error(`❌ [KICK] 断开连接失败:`, e);
        }
    }, 100);

    return res.json({ code: 200, msg: '踢出指令已执行' });
});

// --- 6. Socket.IO 核心业务 ---
io.on('connection', (socket) => {
    console.log('🟢 新连接接入:', socket.id);

    // 监听：加入聊天
    socket.on('join', (userId) => {
        const uid = String(userId);

        onlineUsers.set(uid, socket.id);
        console.log(`👤 用户上线: ${uid} (Socket: ${socket.id})`);

        socket.join(`user_${uid}`); // 加入房间

        io.emit('update_online_count', onlineUsers.size);
    });

    // 监听：发送消息
    socket.on('send_message', async (data) => {
        console.log(`📩 收到消息:`, data);
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
            console.log('✅ 消息已存库');
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
        }
    });

    // 监听：断开连接
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
        } else {
            console.log('🔴 未登录连接断开:', socket.id);
        }

        io.emit('update_online_count', onlineUsers.size);
    });
});

// --- 7. 启动服务器 ---
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🚀 聊天服务器运行在: http://localhost:${PORT}`);
    console.log(`🔌 等待 Flask 踢人指令...`);
});