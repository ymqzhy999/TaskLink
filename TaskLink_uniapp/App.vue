<script>
	import io from '@hyoga/uni-socket.io';

	export default {
		globalData: {
			socket: null,
			userInfo: null,
			isBackground: false // ⚡ 新增：标记 App 是否在后台
		},
		
		onLaunch: function() {
			console.log('App Launch');
			// #ifdef APP-PLUS
			uni.setKeepScreenOn({ keepScreenOn: true });
			// #endif

			const userInfo = uni.getStorageSync('userInfo');
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				this.initSocket();
				uni.switchTab({ url: '/pages/index/index', fail: () => {} });
			} else {
				uni.reLaunch({ url: '/pages/login/login', fail: () => {} });
			}
		},

		// ⚡ 监听页面切入后台 (按 Home 键)
		onHide: function() {
			console.log('App Hide (切后台)');
			this.globalData.isBackground = true;
		},

		// ⚡ 监听页面切回前台
		onShow: function() {
			console.log('App Show (回前台)');
			this.globalData.isBackground = false;
			// 每次回来都清除红点，体验更好
			uni.removeTabBarBadge({ index: 1 });
		},

		methods: {
			initSocket() {
				if (this.globalData.socket) return;

				const userInfo = this.globalData.userInfo;
				const socketUrl = 'http://101.35.132.175:3000'; // ⚠️ 确认 IP
				
				const socket = io(socketUrl, {
					query: { userId: userInfo ? userInfo.id : '' },
					transports: ['websocket', 'polling'],
					timeout: 5000,
				});

				this.globalData.socket = socket;

				socket.on('connect', () => {
					console.log('✅ Socket Connected');
					if (userInfo) socket.emit('join', userInfo.id);
				});

				socket.on('new_message', (msg) => {
					// 1. 忽略自己发的消息
					if (String(msg.user_id) === String(userInfo.id)) return;

					// 2. 核心判断逻辑
					// 如果 App 在后台 -> 直接发系统通知
					if (this.globalData.isBackground) {
						this.sendSystemNotification(msg);
						return; 
					}

					// 3. 如果 App 在前台 -> 判断是否在聊天页
					const pages = getCurrentPages();
					const currentPage = pages[pages.length - 1];
					const isChatPage = currentPage && currentPage.route.includes('pages/square/square');

					if (!isChatPage) {
						// 在 App 内其他页面 -> 显示赛博弹窗
						uni.setTabBarBadge({ index: 1, text: '1' });
						uni.vibrateLong();
						
						// #ifdef APP-PLUS
						this.showCyberpunkNotification(msg.username, msg.content);
						// #endif
						
						// #ifndef APP-PLUS
						uni.showToast({ title: msg.content, icon: 'none' });
						// #endif
					}
				});
			},

			// 🔔 [新增] 发送系统通知栏消息 (后台时用)
			sendSystemNotification(msg) {
				// #ifdef APP-PLUS
				uni.createPushMessage({
					title: `⚡ ${msg.username}`,
					content: msg.content,
					payload: { page: '/pages/square/square' },
					sound: 'system',
					cover: false
				});
				// #endif
			},

			// ⚡ [原有] 赛博朋克应用内弹窗 (前台时用)
			showCyberpunkNotification(title, content) {
				const view = new plus.nativeObj.View('cyberNotify', {
					top: '20px', left: '10px', height: '70px', width: '95%',
					backgroundColor: 'rgba(0,0,0,0.9)'
				});

				view.draw([
					{ tag: 'rect', id: 'border', rect: { top: '0px', left: '0px', width: '100%', height: '100%' }, color: '#00f3ff', style: 'stroke', strokeWidth: '2px' },
					{ tag: 'rect', id: 'line', rect: { top: '5px', left: '5px', width: '3px', height: '60px' }, color: '#ff003c' },
					{ tag: 'font', id: 'title', text: `⚡ INCOMING: ${title}`, textStyles: { size: '14px', color: '#00f3ff', weight: 'bold', align: 'left' }, position: { top: '10px', left: '15px', width: '80%', height: '20px' } },
					{ tag: 'font', id: 'content', text: content, textStyles: { size: '12px', color: '#ffffff', align: 'left', overflow: 'ellipsis' }, position: { top: '35px', left: '15px', width: '80%', height: '30px' } }
				]);

				view.show();
				
				view.addEventListener("click", () => {
					// 点击弹窗跳转到广场
					uni.switchTab({ url: '/pages/square/square' });
					view.close();
				});

				setTimeout(() => { view.close(); }, 4000);
			}
		}
	}
</script>

<style lang="scss">
	@import '@/uni.scss';
	page { background-color: #050505; font-family: 'Courier New', Courier, monospace; color: #e0e0e0; }
</style>