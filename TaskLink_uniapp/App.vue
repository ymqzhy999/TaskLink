<script>
	// 引入 socket 库
	import io from '@hyoga/uni-socket.io';

	export default {
		// 全局变量
		globalData: {
			socket: null,
			userInfo: null
		},
		
		onLaunch: function() {
			console.log('App Launch');

			// #ifdef APP-PLUS
			// 1. 保持屏幕常亮
			uni.setKeepScreenOn({ keepScreenOn: true });
			// 2. 锁定竖屏
			plus.screen.lockOrientation('portrait-primary');
			// #endif

			// 3. 自动登录检测
			const userInfo = uni.getStorageSync('userInfo');
			
			if (userInfo) {
				this.globalData.userInfo = userInfo;
				this.initSocket();

				// 跳转主页
				uni.switchTab({
					url: '/pages/index/index',
					fail: () => {} 
				});
			} else {
				uni.reLaunch({
					url: '/pages/login/login',
					fail: () => {}
				});
			}
		},

// ... existing code ...
		methods: {
			initSocket() {
				if (this.globalData.socket) return;

				const userInfo = this.globalData.userInfo;
				// ⚠️ 确认你的 IP
				const socketUrl = 'http://192.168.10.28:3000'; 
				
				const socket = io(socketUrl, {
					query: { userId: userInfo ? userInfo.id : '' },
					transports: ['websocket', 'polling'],
					timeout: 5000,
				});

				this.globalData.socket = socket;

				socket.on('connect', () => {
					console.log('✅ [App] Socket 已连接');
					if (userInfo) {
						socket.emit('join', userInfo.id);
					}
				});

				// 🔥 核心：收到消息
				socket.on('new_message', (msg) => {
					// 1. 忽略自己发的消息
					if (String(msg.user_id) === String(userInfo.id)) return;

					// 2. 判断当前页面
					const pages = getCurrentPages();
					const currentPage = pages[pages.length - 1];
					const currentRoute = currentPage ? currentPage.route : '';
					const isChatPage = currentRoute.includes('pages/square/square');

					// 如果不在聊天页 -> 执行“赛博式”强提醒
					if (!isChatPage) {
						// A. 设置 TabBar 红点 (假设聊天页 index 为 1)
						uni.setTabBarBadge({
							index: 1, 
							text: '1'
						});
						
						// B. 震动反馈
						uni.vibrateLong();

						// C. ⚡ 调用赛博朋克弹窗 (仅 App 端有效)
						// #ifdef APP-PLUS
						this.showCyberpunkNotification(msg.username, msg.content);
						// #endif

						// H5/小程序端降级处理
						// #ifndef APP-PLUS
						uni.showToast({
							title: `[⚡] ${msg.username}: ${msg.content}`,
							icon: 'none',
							duration: 3000
						});
						// #endif
					}
				});
			},

			// ⚡ [新增] 绘制赛博朋克风格通知栏
			showCyberpunkNotification(title, content) {
				// 1. 创建原生 View (覆盖在最顶层)
				const view = new plus.nativeObj.View('cyberNotify', {
					top: '20px', 
					left: '10px', 
					height: '70px', 
					width: '95%',
					backgroundColor: 'rgba(0,0,0,0.9)' // 半透明黑底
				});

				// 2. 绘制内容 (边框、图标、文字)
				view.draw([
					// 霓虹边框 (Cyan)
					{ tag: 'rect', id: 'border', rect: { top: '0px', left: '0px', width: '100%', height: '100%' }, color: '#00f3ff', style: 'stroke', strokeWidth: '2px' },
					// 装饰线条 (Pink)
					{ tag: 'rect', id: 'line', rect: { top: '5px', left: '5px', width: '3px', height: '60px' }, color: '#ff003c' },
					// 标题 (User)
					{ tag: 'font', id: 'title', text: `⚡ INCOMING: ${title}`, textStyles: { size: '14px', color: '#00f3ff', weight: 'bold', align: 'left' }, position: { top: '10px', left: '15px', width: '80%', height: '20px' } },
					// 内容 (Msg)
					{ tag: 'font', id: 'content', text: content, textStyles: { size: '12px', color: '#ffffff', align: 'left', overflow: 'ellipsis' }, position: { top: '35px', left: '15px', width: '80%', height: '30px' } }
				]);

				// 3. 显示并添加点击事件
				view.show();
				
				// 点击跳转
				view.addEventListener("click", () => {
					uni.switchTab({ url: '/pages/square/square' });
					view.close();
				});

				// 4. 4秒后自动消失
				setTimeout(() => {
					view.close();
				}, 4000);
			}
		}
// ... existing code ...
	}
</script>

<style lang="scss">
	/* 每个页面公共css */
	@import '@/uni.scss';

	/* 全局样式 */
	page {
		background-color: #050505;
		font-family: 'Courier New', Courier, monospace;
		color: #e0e0e0;
	}
</style>