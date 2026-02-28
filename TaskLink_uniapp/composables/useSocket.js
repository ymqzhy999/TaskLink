import io from '@hyoga/uni-socket.io'
import { SOCKET_URL } from '../utils/api.js'

/**
 * Socket 连接管理
 * 抽离出来以后就不用在每个页面写一堆连接逻辑了
 */
const useSocket = () => {
  // 存当前的 socket 实例
  let socket = null
  // 防止重复连接
  let isConnecting = false

  /**
   * 初始化 socket 连接
   * 只连一次，后续都复用
   */
  const initSocket = () => {
    // 已经连上了就别折腾
    if (socket && socket.connected) {
      return socket
    }

    // 正在连呢，别重复触发
    if (isConnecting) {
      return null
    }

    // 检查有没有用户信息，没有就不连
    const userInfo = uni.getStorageSync('userInfo')
    if (!userInfo) {
      return null
    }

    isConnecting = true
    console.log('🔵 开始连 Socket:', SOCKET_URL)

    // 先把旧的断了，防止内存泄漏
    if (socket) {
      try {
        socket.close()
      } catch (e) {
        console.warn('关掉旧 socket 失败了', e)
      }
      socket = null
    }

    try {
      // 建新连接
      socket = io(SOCKET_URL, {
        query: {
          userId: userInfo.id,
          token: userInfo.token
        },
        // 强制走 websocket，别搞轮询
        transports: ['websocket'],
        timeout: 20000,
        // 自动重连配置
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 3000,
        forceNew: true
      })

      // 监听连接成功
      socket.on('connect', () => {
        console.log('✅ Socket 连上了:', socket.id)
        isConnecting = false
        // 告诉服务器我进来了
        socket.emit('join', { user_id: userInfo.id })
      })

      // 监听断开
      socket.on('disconnect', (reason) => {
        console.log('🔴 Socket 断了:', reason)
        isConnecting = false
      })

      // 监听连接失败
      socket.on('connect_error', (error) => {
        console.log('⚠️ Socket 连接失败:', error)
        isConnecting = false
      })

      // 监听新消息
      socket.on('new_message', (msg) => {
        // 发给全局，用的地方自己订阅
        uni.$emit('global_new_message', msg)
        //顺带处理通知
        handleNotification(msg)
      })

      // 监听在线人数
      socket.on('update_online_count', (count) => {
        uni.$emit('global_online_count', count)
      })

      return socket
    } catch (e) {
      console.error('Socket 初始化炸了:', e)
      isConnecting = false
      return null
    }
  }

  /**
   * 发消息用的
   * @param {string} event - 事件名
   * @param {any} data - 要发的数据
   */
  const emit = (event, data) => {
    if (socket && socket.connected) {
      socket.emit(event, data)
    } else {
      console.warn('Socket 没连上，发不出去:', event)
    }
  }

  /**
   * 监听事件
   * @param {string} event - 事件名
   * @param {function} callback - 回调
   */
  const on = (event, callback) => {
    if (socket) {
      socket.on(event, callback)
    }
  }

  /**
   * 取消监听
   * @param {string} event - 事件名
   * @param {function} callback - 回调
   */
  const off = (event, callback) => {
    if (socket) {
      socket.off(event, callback)
    }
  }

  /**
   * 主动断开连接
   * 一般 App 切后台时可能用到
   */
  const disconnect = () => {
    if (socket) {
      socket.disconnect()
      socket = null
    }
  }

  /**
   * 处理新消息通知
   * 判断一下当前页面，决定要不要弹通知
   */
  const handleNotification = (msg) => {
    const userInfo = uni.getStorageSync('userInfo')
    // 自己发的消息不管
    if (!userInfo || String(msg.user_id) === String(userInfo.id)) {
      return
    }

    // 正在广场页面且在前台，不弹
    const app = getApp()
    if (app?.globalData?.isSquareOpen && !app?.globalData?.isBackground) {
      return
    }

    // 震动一下提醒
    uni.vibrateLong({ fail: () => {} })

    // TabBar 右上角小红点
    try {
      uni.setTabBarBadge({ index: 1, text: '1', fail: () => {} })
    } catch (e) {}

    // App 端本地通知
    // #ifdef APP-PLUS
    createLocalNotification(msg)
    // #endif
  }

  /**
   * 创建本地通知（App 专享）
   */
  const createLocalNotification = (msg) => {
    // 处理消息内容，太长截断
    const content = msg.type === 'image'
      ? '[图片消息]'
      : (msg.content && msg.content.length > 30 ? msg.content.substring(0, 30) + '...' : msg.content)

    // 标题
    const title = msg.is_bot ? '🤖 波比' : (msg.username || '新消息')

    const options = {
      title: title,
      content: content,
      payload: JSON.stringify(msg), // 点击时带着这个消息的数据
      delay: 0,
      force: true,
      sound: 'system'
    }

    try {
      plus.push.createMessage(options.title, options.content, options)
      console.log('✅ 本地通知安排上了:', title)
    } catch (e) {
      console.error('❌ 本地通知挂了:', e)
    }
  }

  return {
    initSocket,
    emit,
    on,
    off,
    disconnect,
    // 顺便把 socket 实例暴露出去，方便直接操作
    get socket() { return socket }
  }
}

export default useSocket
