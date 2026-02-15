<script>
	import io from '@hyoga/uni-socket.io';

	const SOCKET_URL = `http://101.35.132.175:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false,
			isSquareOpen: false
		},
		
		
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
				this.initSocket(); 
				

				uni.switchTab({
					url: '/pages/index/index',
					fail: () => {
						uni.reLaunch({ url: '/pages/index/index' });
					}
				});
			} else {
				uni.reLaunch({ url: '/pages/login/login' });
			}
		},

		onShow: function() {
			this.globalData.isBackground = false;
			
			// 检查 Socket 状态，如果断开且不处于连接中，尝试补救
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
							token: userInfo.token 
						},
						transports: ['websocket'], // 🔥 核心：强制 WebSocket
						timeout: 20000,
						reconnection: true,
						reconnectionAttempts: 10,
						reconnectionDelay: 3000,
						forceNew: true
					});

					this.globalData.socket = socket;

					// --- 监听事件 ---
					socket.on('connect', () => {
						console.log('✅ [Socket] 连接成功 ID:', socket.id);
						this._isConnecting = false;
						socket.emit('join', { user_id: userInfo.id });
					});

					socket.on('disconnect', (reason) => {
						console.log('🔴 [Socket] 断开:', reason);
						this._isConnecting = false;
					});
					
					socket.on('connect_error', (error) => {
						console.log('⚠️ [Socket] 连接错误:', error);
						this._isConnecting = false;
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
				
				if (this.globalData.isSquareOpen && !this.globalData.isBackground) return;

				uni.vibrateLong({ fail: () => {} });
				
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
		background-color: #F5F5F0 !important; /* 浅米色 */
		color: #2C3E50; /* 深灰文字 */
		font-family: 'Inter', -apple-system, Helvetica, sans-serif;
		height: 100%;
	}

	uni-page-body {
		background-color: #F5F5F0 !important;
		height: 100%;
		min-height: 100vh;
	}
	
	::-webkit-scrollbar {
		display: none;
		width: 0;
		height: 0;
	}
</style>