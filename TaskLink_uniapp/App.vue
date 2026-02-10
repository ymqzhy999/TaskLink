<script>
	import io from '@hyoga/uni-socket.io';

	const SERVICE_HOST = import.meta.env.VITE_SERVICE_HOST || '127.0.0.1';
	const SOCKET_URL = `http://${SERVICE_HOST}:3000`;

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false,
			isSquareOpen: false
		},
		
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
				this.initSocket();
			} else {
				uni.reLaunch({ url: '/pages/login/login' });
			}
		},

		onShow: function() {
			this.globalData.isBackground = false;
			// 检查连接，断线重连
			this.initSocket();
		},

		onHide: function() {
			this.globalData.isBackground = true;
		},

		methods: {
			initSocket() {
				const app = getApp();
				
				// 🔥【核心修改】如果已经连接，直接返回，绝对不连第二次
				if (app.globalData.socket && app.globalData.socket.connected) {
					return; 
				}
				
				// 防止短时间内重复调用
				if (this._isConnecting) return;
				this._isConnecting = true;

				const userInfo = uni.getStorageSync('userInfo');
				if (!userInfo) return;

				console.log('🔵 [App.vue] 发起连接:', SOCKET_URL);
				
				// 强制只允许一个连接实例
				if (app.globalData.socket) {
					app.globalData.socket.disconnect();
					app.globalData.socket = null;
				}

				const socket = io(SOCKET_URL, {
					query: { userId: userInfo.id },
					transports: ['websocket', 'polling'],
					timeout: 10000,
					forceNew: false // 改为 false，尝试复用
				});

				app.globalData.socket = socket;

				socket.on('connect', () => {
					console.log('✅ [App.vue] Socket Connected ID:', socket.id);
					this._isConnecting = false;
					socket.emit('join', userInfo.id);
				});
				
				socket.on('disconnect', () => {
					console.log('🔴 [App.vue] Socket Disconnected');
					this._isConnecting = false;
				});
				
				socket.on('connect_error', () => {
					this._isConnecting = false;
				});

				// 监听消息
				socket.on('new_message', (msg) => {
					// 1. 先广播 (square.vue 接收)
					uni.$emit('global_new_message', msg);

					// 2. 自己发的不弹窗
					if (String(msg.user_id) === String(userInfo.id)) return;

					// 3. 处理通知
					this.handleNotification(msg);
				});
				
				// 监听在线人数广播
				socket.on('update_online_count', (count) => {
					uni.$emit('global_online_count', count);
				});
			},

			handleNotification(msg) {
				const shouldNotify = this.globalData.isBackground || !this.globalData.isSquareOpen;
				if (shouldNotify) {
					uni.vibrateLong();
					uni.setTabBarBadge({ index: 1, text: '1' });
					// #ifdef APP-PLUS
					const content = msg.type === 'image' ? '[图片]' : msg.content;
					plus.push.createMessage(`${msg.username}: ${content}`, { type: 'chat' }, { title: "TaskLink", cover: false });
					// #endif
				}
			}
		}
	}
</script>
<style lang="scss">
	@import '@/uni.scss';
	page { background-color: #050505; font-family: 'Courier New', monospace; color: #e0e0e0; }
</style>