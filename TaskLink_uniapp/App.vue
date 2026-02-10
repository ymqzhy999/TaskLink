<script>
	// 引入 Socket.io
	import io from '@hyoga/uni-socket.io';

	// 使用 .env 配置，没有则回退
	const SERVICE_HOST = import.meta.env.VITE_SERVICE_HOST || '127.0.0.1';
	const SOCKET_URL = `http://${SERVICE_HOST}:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null
		},
		
		onLaunch: function() {
			console.log('App Launch');
			
			// 1. 锁定竖屏 (仅 App 端)
			// #ifdef APP-PLUS
			plus.screen.lockOrientation('portrait-primary');
			// #endif

			// 2. 检查登录状态
			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				// 如果已登录，初始化 Socket 并跳转首页
				this.initSocket();
				uni.switchTab({ url: '/pages/index/index' });
			} else {
				// 未登录，跳转登录页
				uni.reLaunch({ url: '/pages/login/login' });
			}
		},

		onShow: function() {
			console.log('App Show');
			// 每次切回前台，检查 Socket 是否断开，断开则重连
			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.initSocket();
			}
		},

		onHide: function() {
			console.log('App Hide');
		},

		methods: {
			initSocket() {
				// 防止重复连接
				if (this.globalData.socket && this.globalData.socket.connected) return;

				const userInfo = uni.getStorageSync('userInfo');
				if (!userInfo) return;

				console.log('🔵 连接 Socket:', SOCKET_URL);
				
				const socket = io(SOCKET_URL, {
					query: { userId: userInfo.id },
					transports: ['websocket', 'polling'],
					timeout: 5000,
					forceNew: true
				});

				this.globalData.socket = socket;

				socket.on('connect', () => {
					console.log('✅ Socket Connected ID:', socket.id);
					socket.emit('join', userInfo.id);
				});
				
				// 监听消息，只负责分发事件
				socket.on('new_message', (msg) => {
					// 广播给页面 (square.vue) 处理
					uni.$emit('global_new_message', msg);
				});
			}
		}
	}
</script>

<style lang="scss">

	
	
@import '@/uni.scss';	
	// 设置整个应用的背景色
	page {
		background-color: #050505;
		font-family: 'Courier New', Courier, monospace;
		color: #e0e0e0;
	}
	/* #endif */
</style>