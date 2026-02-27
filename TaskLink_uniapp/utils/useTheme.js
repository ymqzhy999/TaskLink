import { ref } from 'vue';
import { onShow, onUnload } from '@dcloudio/uni-app';

// TabBar 页面路径
const TAB_BAR_PAGES = ['pages/index/index', 'pages/dict/dict', 'pages/plan/plan', 'pages/profile/profile'];

export function useTheme() {
  const isDarkMode = ref(false);

  // 检查当前页面是否是 TabBar 页面
  const isTabBarPage = () => {
    const pages = getCurrentPages();
    if (pages.length === 0) return false;
    const currentPage = pages[pages.length - 1];
    return TAB_BAR_PAGES.some(path => currentPage.route && currentPage.route.includes(path));
  };

  const applyTheme = (dark) => {
    isDarkMode.value = dark;
    
    // 设置导航栏颜色
    if (dark) {
      uni.setNavigationBarColor({
        frontColor: '#ffffff',
        backgroundColor: '#121212',
        animation: { duration: 300, timingFunc: 'easeIn' }
      });
      // 只在 TabBar 页面设置 TabBar 样式
      if (isTabBarPage()) {
        uni.setTabBarStyle({
          backgroundColor: '#1E1E1E',
          color: '#888888',
          selectedColor: '#4A6FA5',
          borderStyle: 'black'
        });
      }
    } else {
      uni.setNavigationBarColor({
        frontColor: '#000000',
        backgroundColor: '#ffffff',
        animation: { duration: 300, timingFunc: 'easeIn' }
      });
      // 只在 TabBar 页面设置 TabBar 样式
      if (isTabBarPage()) {
        uni.setTabBarStyle({
          backgroundColor: '#ffffff',
          color: '#666666',
          selectedColor: '#4A6FA5',
          borderStyle: 'white'
        });
      }
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
