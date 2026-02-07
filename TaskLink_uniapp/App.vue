<script>
	export default {
		onLaunch: function() {
			console.log('App Launch');
            // 保持屏幕常亮
            uni.setKeepScreenOn({ keepScreenOn: true });

            // 自动登录检测
            const userInfo = uni.getStorageSync('userInfo');
            if (userInfo) {
                // 有用户信息，直接跳转主页
                uni.switchTab({ url: '/pages/index/index' });
            }
		}
	}
</script>

<style>
    /* 全局背景色，防止切换闪烁 */
    page {
        background-color: #050505;
        font-family: 'Courier New', Courier, monospace;
    }
</style>