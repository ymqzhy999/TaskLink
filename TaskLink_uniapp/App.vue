<script>
	import io from '@hyoga/uni-socket.io';

	// 建议提取到 common/config.js
	const SOCKET_URL = `http://101.35.132.175:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false
		},
		
		// 加上这个锁，防止重复连接
		_isConnecting: false,
		
		onLaunch: function() {
			// #ifdef APP-PLUS
			plus.screen.lockOrientation('portrait-primary');
			plus.push.addEventListener('click', () => {
				setTimeout(() => uni.switchTab({ url: '/pages/square/square' }), 500);
			}, false);
			// #endif

			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				// 仅在 Launch 时初始化一次，不要在 onShow 里疯狂调用
				this.connectSocket(); 
				
				// 自动跳转
				uni.switchTab({
					url: '/pages/index/index',
					fail: () => uni.reLaunch({ url: '/pages/index/index' })
				});
			} else {
				uni.reLaunch({ url: '/pages/login/login' });
			}
		},

		onShow: function() {
			this.globalData.isBackground = false;
			// ⚠️⚠️⚠️ 严重警告：
			// 不要在这里调用 connectSocket() 或 checkSocket()
			// 否则一旦断网，onShow 会和 Socket 错误回调形成死循环，导致 App 闪退
		},

		onHide: function() {
			this.globalData.isBackground = true;
		},

		methods: {
			connectSocket() {
				// 1. 基础检查
				if (this._isConnecting) return;
				const userInfo = uni.getStorageSync('userInfo');
				if (!userInfo) return;

				// 2. 如果已连接，直接跳过
				if (this.globalData.socket && this.globalData.socket.connected) {
					return;
				}

				this._isConnecting = true;
				console.log('🔵 [Socket] 开始连接:', SOCKET_URL);

				// 3. 清理旧连接
				if (this.globalData.socket) {
					try {
						this.globalData.socket.close();
						this.globalData.socket = null;
					} catch(e) {}
				}

				try {
					// 4. 创建新连接
					const socket = io(SOCKET_URL, {
						query: { userId: userInfo.id },
						transports: ['websocket'], // 🔥 强制只用 websocket，禁用 polling，防止死循环
						timeout: 10000,
						reconnection: true,
						reconnectionAttempts: 10, // 限制重连次数
						reconnectionDelay: 3000,  // 重连间隔 3秒
						forceNew: false
					});

					this.globalData.socket = socket;

					// --- 监听事件 ---
					socket.on('connect', () => {
						console.log('✅ [Socket] 已连接 ID:', socket.id);
						this._isConnecting = false;
						socket.emit('join', userInfo.id);
					});

					socket.on('disconnect', (reason) => {
						console.log('🔴 [Socket] 断开:', reason);
						this._isConnecting = false;
					});
					
					socket.on('connect_error', (error) => {
						console.log('⚠️ [Socket] 连接错误:', error);
						this._isConnecting = false;
						// 不要在这里 alert 或 toast，否则会触发 onShow 死循环
					});

					// 监听新消息
					socket.on('new_message', (msg) => {
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

				const shouldNotify = this.globalData.isBackground; 
				if (shouldNotify) {
					// 仅震动，不弹窗，防止干扰
					uni.vibrateLong({ fail: () => {} });
					
					// 安全设置 TabBar 角标
					try {
						uni.setTabBarBadge({ index: 1, text: '1', fail: () => {} });
					} catch(e) {}
				}
			}
		}
	}
</script>

<style lang="scss">
	@import '@/uni.scss';
	page { 
		background-color: #f5f7fa; /* 改为浅色背景配合新 UI */
		font-family: 'Courier New', monospace; 
		color: #333; 
	}
</style>