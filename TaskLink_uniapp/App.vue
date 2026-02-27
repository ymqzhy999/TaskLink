<script>
	import io from '@hyoga/uni-socket.io';

	const SOCKET_URL = `http://101.35.132.175:3000`;

	export default {		
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false,
			isSquareOpen: false,
			isDarkMode: false // 全局深色模式状态
		},
		
		_isConnecting: false,
		
		data() {
			return {
			};
		},
		
		onLaunch: function() {
			// #ifdef APP-PLUS
			plus.screen.lockOrientation('portrait-primary');
			// 处理推送点击
			plus.push.addEventListener('click', (msg) => {
				setTimeout(() => uni.switchTab({ url: '/pages/square/square' }), 500);
			}, false);
			// #endif

			// 1. 初始化用户信息
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
			
			// 2. 初始化深色模式
			const theme = uni.getStorageSync('theme');
			if (theme === 'dark') {
				this.setDarkMode(true);
			} else {
				this.setDarkMode(false);
			}
			
			// 监听全局主题切换事件
			uni.$on('toggleTheme', (isDark) => {
				console.log('App.vue 收到 toggleTheme 事件:', isDark);
				this.setDarkMode(isDark);
			});
		},

		onShow: function() {
			this.globalData.isBackground = false;
			
			// 检查 Socket 状态
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
			setDarkMode(isDark) {
				console.log('App.vue 执行 setDarkMode:', isDark);
				this.globalData.isDarkMode = isDark;
				uni.setStorageSync('theme', isDark ? 'dark' : 'light');
				
				// 使用 try-catch 包装，避免在 H5 环境下某些 API 不支持导致的错误
				try {
					if (isDark) {
						// #ifdef H5
						// H5 环境下，导航栏颜色设置可能不支持，使用 document 方式
						if (typeof document !== 'undefined') {
							const metaTheme = document.querySelector('meta[name="theme-color"]');
							if (metaTheme) {
								metaTheme.setAttribute('content', '#121212');
							} else {
								const meta = document.createElement('meta');
								meta.name = 'theme-color';
								meta.content = '#121212';
								document.head.appendChild(meta);
							}
						}
						// #endif
						
						// #ifndef H5
						uni.setNavigationBarColor({
							frontColor: '#ffffff',
							backgroundColor: '#121212'
						});
						// 只在 TabBar 页面设置样式
						const pages = getCurrentPages();
						const currentPage = pages[pages.length - 1];
						const tabBarPages = ['pages/index/index', 'pages/plan/plan', 'pages/vocab/vocab', 'pages/profile/profile'];
						if (currentPage && tabBarPages.some(p => currentPage.route && currentPage.route.includes(p))) {
							uni.setTabBarStyle({
								backgroundColor: '#1E1E1E',
								color: '#888888',
								selectedColor: '#4A6FA5',
								borderStyle: 'black'
							});
						}
						// #endif
					} else {
						// #ifdef H5
						if (typeof document !== 'undefined') {
							const metaTheme = document.querySelector('meta[name="theme-color"]');
							if (metaTheme) {
								metaTheme.setAttribute('content', '#ffffff');
							}
						}
						// #endif
						
						// #ifndef H5
						uni.setNavigationBarColor({
							frontColor: '#000000',
							backgroundColor: '#ffffff'
						});
						// 只在 TabBar 页面设置样式
						const pages2 = getCurrentPages();
						const currentPage2 = pages2[pages2.length - 1];
						const tabBarPages = ['pages/index/index', 'pages/plan/plan', 'pages/vocab/vocab', 'pages/profile/profile'];
						if (currentPage2 && tabBarPages.some(p => currentPage2.route && currentPage2.route.includes(p))) {
							uni.setTabBarStyle({
								backgroundColor: '#ffffff',
								color: '#666666',
								selectedColor: '#4A6FA5',
								borderStyle: 'white'
							});
						}
						// #endif
					}
				} catch (error) {
					console.warn('设置深色模式时出错:', error);
					// 即使出错也不影响主题状态
				}
			},

			initSocket() {
				// ... (保持原有 Socket 逻辑不变)
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
	
	/* 全局样式动态切换 */
	page {
		transition: background-color 0.3s, color 0.3s;
	}
	
	/* 默认(浅色) */
	page {
		background-color: #F5F5F0; /* 移除 !important */
		color: #2C3E50;
		font-family: 'Inter', -apple-system, Helvetica, sans-serif;
		height: 100%;
	}

	uni-page-body {
		background-color: #F5F5F0; /* 移除 !important */
		height: 100%;
		min-height: 100vh;
	}
	
	/* 深色模式全局样式 (通过在 body/page 上加 class 实现较难，通常是在页面最外层 view 加 .dark) 
	   但在 App.vue 这里主要定义全局 CSS 变量或默认样式 
	*/
	
	::-webkit-scrollbar {
		display: none;
		width: 0;
		height: 0;
	}
</style>