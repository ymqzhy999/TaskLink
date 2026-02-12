<script>
	import io from '@hyoga/uni-socket.io';

	// 建议提取到单独的配置文件中
	const SOCKET_URL = `http://101.35.132.175:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false,
			isSquareOpen: false // 标记广场页是否打开
		},
		
		// 内部状态标记，不放在 globalData 里
		_isConnecting: false,
		
		onLaunch: function() {
			// #ifdef APP-PLUS
			plus.screen.lockOrientation('portrait-primary');
			// 点击通知栏消息的逻辑
			plus.push.addEventListener('click', (msg) => {
				// 这里可以解析 msg.payload 跳转到具体聊天窗口
				setTimeout(() => uni.switchTab({ url: '/pages/square/square' }), 500);
			}, false);
			// #endif

			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				console.log('检测到已登录，准备跳转...');
				
				// 放在这里初始化，如果在 switchTab 之后再初始化可能会有瞬间的延迟
				// 但要注意 onShow 也会触发
				this.initSocket(); 

				uni.switchTab({
					url: '/pages/index/index',
					fail: () => {
						// 容错处理
						uni.reLaunch({ url: '/pages/index/index' });
					}
				});
			} else {
				uni.reLaunch({ url: '/pages/login/login' });
			}
		},

		onShow: function() {
			this.globalData.isBackground = false;
			// 每次切回前台，检查一下 Socket 状态
			this.checkSocketConnection();
		},

		onHide: function() {
			this.globalData.isBackground = true;
		},

		methods: {
			/**
			 * 检查并尝试重连
			 * 这是一个轻量级的方法，用于 onShow 调用
			 */
			checkSocketConnection() {
				const socket = this.globalData.socket;
				const userInfo = uni.getStorageSync('userInfo');
				
				// 如果没有用户信息，不连接
				if (!userInfo) return;

				// 如果 socket 不存在，或者断开了，则重新初始化
				if (!socket || !socket.connected) {
					console.log('🔄 [App.vue] 状态检查：Socket未连接，尝试重连...');
					this.initSocket();
				}
			},

			initSocket() {
				// 1. 防止重复连接锁
				if (this._isConnecting) return;
				
				const userInfo = uni.getStorageSync('userInfo');
				if (!userInfo) return;

				// 2. 如果当前已经连接正常，直接返回
				if (this.globalData.socket && this.globalData.socket.connected) {
					console.log('✅ [App.vue] Socket 已连接，无需操作');
					return; 
				}

				this._isConnecting = true;
				console.log('🔵 [App.vue] 发起连接:', SOCKET_URL);

				// 3. 彻底清理旧连接 (关键：防止多重监听)
				if (this.globalData.socket) {
					this.globalData.socket.removeAllListeners(); // 移除所有监听器
					this.globalData.socket.disconnect();
					this.globalData.socket = null;
				}

				// 4. 创建新实例
				try {
					const socket = io(SOCKET_URL, {
						query: { userId: userInfo.id },
						transports: ['websocket', 'polling'],
						timeout: 10000,
						reconnection: true, // 启用内置重连机制
						reconnectionAttempts: 5, // 限制重连次数
						forceNew: true // 建议为 true，确保拿到全新的实例
					});

					// 绑定到全局
					this.globalData.socket = socket;

					// --- 监听事件 ---

					socket.on('connect', () => {
						console.log('✅ [App.vue] Socket Connected ID:', socket.id);
						this._isConnecting = false;
						socket.emit('join', userInfo.id);
					});
					
					socket.on('disconnect', (reason) => {
						console.log('🔴 [App.vue] Socket Disconnected:', reason);
						this._isConnecting = false;
						// 如果是服务器强制断开，可能需要重置 socket = null
						if (reason === 'io server disconnect') {
							socket.connect(); // 手动重连
						}
					});
					
					socket.on('connect_error', (err) => {
						console.log('⚠️ [App.vue] Connection Error:', err);
						this._isConnecting = false;
					});

					// 监听消息
					socket.on('new_message', (msg) => {
						this.handleNewMessage(msg, userInfo);
					});
					
					// 监听在线人数广播
					socket.on('update_online_count', (count) => {
						uni.$emit('global_online_count', count);
					});

				} catch (e) {
					console.error('Socket 初始化异常:', e);
					this._isConnecting = false;
				}
			},

			handleNewMessage(msg, userInfo) {
				// 1. 全局广播 (无论页面在哪里，都把消息发出去，页面自己决定是否处理)
				uni.$emit('global_new_message', msg);

				// 2. 过滤自己发的消息
				// 注意：msg.user_id 和 userInfo.id 类型可能不一致(string/number)，建议统一转 String
				if (String(msg.user_id) === String(userInfo.id)) return;

				// 3. 处理通知和角标
				const shouldNotify = this.globalData.isBackground || !this.globalData.isSquareOpen;
				
				if (shouldNotify) {
					// 震动
					uni.vibrateLong({
						fail: () => {} // 某些机型可能不支持，防止报错
					});

					// 设置角标 (增加 try-catch 防止在非 Tab 页报错)
					uni.setTabBarBadge({
						index: 1, 
						text: '1',
						fail: () => {
							// console.log('当前非Tab页面，无法设置角标');
						}
					});

					// #ifdef APP-PLUS
					const content = msg.type === 'image' ? '[图片]' : msg.content;
					// 确保 title 和 content 是字符串
					plus.push.createMessage(
						`${msg.username || '新消息'}: ${content}`, 
						{ type: 'chat', data: msg }, // payload 可以放 msg 对象
						{ title: "TaskLink", cover: false }
					);
					// #endif
				}
			}
		}
	}
</script>

<style lang="scss">
	@import '@/uni.scss';
	page { 
		background-color: #050505; 
		font-family: 'Courier New', monospace; 
		color: #e0e0e0; 
	}
</style>