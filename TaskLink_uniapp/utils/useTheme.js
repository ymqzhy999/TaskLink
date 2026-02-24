import { ref } from 'vue';
import { onShow, onUnload } from '@dcloudio/uni-app';

export function useTheme() {
  const isDarkMode = ref(false);

  const applyTheme = (dark) => {
    isDarkMode.value = dark;
    
    // 设置导航栏颜色 (适配原生导航栏页面)
    if (dark) {
      uni.setNavigationBarColor({
        frontColor: '#ffffff',
        backgroundColor: '#121212',
        animation: { duration: 300, timingFunc: 'easeIn' }
      });
      uni.setTabBarStyle({
        backgroundColor: '#1E1E1E',
        color: '#888888',
        selectedColor: '#4A6FA5',
        borderStyle: 'black'
      });
    } else {
      uni.setNavigationBarColor({
        frontColor: '#000000',
        backgroundColor: '#ffffff', // 或 #F5F5F0
        animation: { duration: 300, timingFunc: 'easeIn' }
      });
      uni.setTabBarStyle({
        backgroundColor: '#ffffff',
        color: '#666666',
        selectedColor: '#4A6FA5',
        borderStyle: 'white'
      });
    }
  };

  const updateTheme = () => {
    const theme = uni.getStorageSync('theme');
    applyTheme(theme === 'dark');
  };

  onShow(() => {
    updateTheme();
    // 监听全局事件
    uni.$on('toggleTheme', applyTheme);
  });

  onUnload(() => {
    uni.$off('toggleTheme', applyTheme);
  });

  return {
    isDarkMode
  };
}
