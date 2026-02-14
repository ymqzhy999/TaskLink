<script>
	import io from '@hyoga/uni-socket.io';

	// 建议提取到 common/config.js
	// 注意：真机调试必须用电脑局域网 IP，不能用 localhost
	const SOCKET_URL = `http://101.35.132.175:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false,
			isSquareOpen: false // 配合 square 页面使用的状态标记
		},
		
		// 连接锁，防止并发重复连接
		_isConnecting: false,
		
		onLaunch: function() {
			// #ifdef APP-PLUS
			plus.screen.lockOrientation('portrait-primary');
			// 处理推送点击
			plus.push.addEventListener('click', (msg) => {
				setTimeout(() => uni.switchTab({ url: '/pages/square/square' }), 500);
			}, false);
			// #endif

			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				// 初始化连接
				this.initSocket(); 
				
				// 自动跳转主页
				/* 注意：如果你的首页是 tabbar 页面，用 switchTab；如果是普通页面用 reLaunch */
				// uni.switchTab({
				// 	url: '/pages/index/index',
				// 	fail: () => uni.reLaunch({ url: '/pages/index/index' })
				// });
			} else {
				// 未登录时不强制跳转，交给 pages.json 的默认规则或 login 页处理
			}
		},

		onShow: function() {
			this.globalData.isBackground = false;
			
			// 检查 Socket 状态，如果断开且不处于连接中，尝试补救
			// 注意：这里不做强制重连，防止死循环，强制重连交给 square.vue 的 onShow
			const socket = this.globalData.socket;
			if (socket && !socket.connected && !this._isConnecting) {
				console.log('App onShow 检测到断线，尝试恢复...');
				socket.connect();
			}
		},

		onHide: function() {
			this.globalData.isBackground = true;
		},

		methods: {
			// 🔥 改名为 initSocket 以匹配 square.vue 的调用
			initSocket() {
				// 1. 基础检查
				if (this._isConnecting) return;
				const userInfo = uni.getStorageSync('userInfo');
				if (!userInfo) return;

				// 2. 如果已连接，直接跳过
				if (this.globalData.socket && this.globalData.socket.connected) {
					console.log('Socket 已连接，跳过初始化');
					return;
				}

				this._isConnecting = true;
				console.log('🔵 [Socket] 开始初始化:', SOCKET_URL);

				// 3. 清理旧连接 (防止内存泄漏)
				if (this.globalData.socket) {
					try {
						this.globalData.socket.close();
						this.globalData.socket = null;
					} catch(e) {}
				}

				try {
					// 4. 创建新连接
					const socket = io(SOCKET_URL, {
						query: { 
							userId: userInfo.id,
							token: userInfo.token // 建议带上 token 供后端校验
						},
						transports: ['websocket'], // 🔥 核心：强制 WebSocket，解决 Android 兼容性
						timeout: 20000,
						reconnection: true,
						reconnectionAttempts: 10,
						reconnectionDelay: 3000,
						forceNew: true // 强制创建新实例
					});

					this.globalData.socket = socket;

					// --- 监听事件 ---
					socket.on('connect', () => {
						console.log('✅ [Socket] 连接成功 ID:', socket.id);
						this._isConnecting = false;
						// 连接后重新加入房间或同步状态
						socket.emit('join', { user_id: userInfo.id });
					});

					socket.on('disconnect', (reason) => {
						console.log('🔴 [Socket] 断开:', reason);
						this._isConnecting = false;
						// 如果是服务器强制断开，可能需要踢出登录
						if (reason === 'io server disconnect') {
							// socket.connect(); // 视情况是否需要手动重连
						}
					});
					
					socket.on('connect_error', (error) => {
						console.log('⚠️ [Socket] 连接错误:', error);
						this._isConnecting = false;
					});

					// 监听新消息 (全局总线转发)
					socket.on('new_message', (msg) => {
						// 通过 uni.$emit 广播给 square.vue
						uni.$emit('global_new_message', msg);
						this.handleNotification(msg);
					});
					
					// 监听在线人数
					socket.on('update_online_count', (count) => {
						uni.$emit('global_online_count', count);
					});

				} catch (e) {
					console.error('Socket 初始化异常:', e);
					this._isConnecting = false;
				}
			},

			handleNotification(msg) {
				const userInfo = this.globalData.userInfo;
				if (!userInfo || String(msg.user_id) === String(userInfo.id)) return;
				
				if (this.globalData.isSquareOpen && !this.globalData.isBackground) return;

				uni.vibrateLong({ fail: () => {} });
				
				// 设置 TabBar 红点
				try {
					uni.setTabBarBadge({ index: 1, text: '1', fail: () => {} });
				} catch(e) {}
			}
		}
	}
</script>

<style lang="scss">
	@import '@/uni.scss';
	page { 
		background-color: #050505; /* 保持赛博黑背景 */
		font-family: 'Courier New', monospace; 
		color: #e0e0e0; 
	}
</style>