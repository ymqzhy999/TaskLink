import App from './App'
import { createSSRApp } from 'vue'

// 引入 Socket.io
import io from '@hyoga/uni-socket.io';

export function createApp() {
  const app = createSSRApp(App)
  
  // 🔥 定义全局 Socket 对象 (挂载到 Vue 原型或 globalProperties)
  app.config.globalProperties.$socket = null;
  app.config.globalProperties.$io = io; // 把 io 构造函数也挂载出去

  return {
    app
  }
}