import { API_BASE } from './api.js'

/**
 * 统一的请求方法，比原生 uni.request 更省心
 * 自动带 token，自动处理登录过期
 * 
 * @param {string} url - 接口路径，不用写完整域名
 * @param {object} options - 配置项，跟 uni.request 差不多
 */
const request = (url, options = {}) => {
  // 拿 token，带上准没错
  const userInfo = uni.getStorageSync('userInfo')
  const token = userInfo?.token || ''

  // 合并配置
  const defaultOptions = {
    url: `${API_BASE}${url}`,
    header: {
      'Authorization': token,
      'Content-Type': 'application/json',
      ...options.header
    },
    timeout: 15000, // 15秒超时，正常够用了
    ...options
  }

  return new Promise((resolve, reject) => {
    // 真正发请求
    uni.request({
      ...defaultOptions,
      success: (res) => {
        // 业务层面的错误处理
        const { statusCode, data } = res
        
        // 状态码不是 200 说明有毛病
        if (statusCode !== 200) {
          handleError(statusCode, data)
          reject(res)
          return
        }

        // 业务返回 code 不是 200，说明后端判定有问题
        if (data.code !== 200) {
          // 登录过期或账号被禁用
          if (data.code === 401 || data.code === 403) {
            handleAuthError()
            reject(new Error(data.msg || '会话过期'))
            return
          }
          
          // 其他业务错误，直接抛出去让调用方处理
          reject(new Error(data.msg || '请求失败'))
          return
        }

        // 一切正常，返回数据
        resolve(data.data)
      },
      fail: (err) => {
        // 网络层面的错误
        console.error('网络请求挂了:', err)
        uni.showToast({
          title: '网络开小差了',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// 处理非 200 的 HTTP 状态码
const handleError = (statusCode, data) => {
  const msgMap = {
    400: '参数不对',
    401: '未登录',
    403: '没权限',
    404: '接口不存在',
    500: '服务器炸了'
  }
  const msg = msgMap[statusCode] || '请求失败'
  uni.showToast({ title: msg, icon: 'none' })
}

// 处理登录过期
const handleAuthError = () => {
  uni.showToast({ title: '登录过期了', icon: 'none' })
  setTimeout(() => {
    uni.removeStorageSync('userInfo')
    uni.reLaunch({ url: '/pages/login/login' })
  }, 1500)
}

// 简写版本
export const get = (url, data) => request(url, { method: 'GET', data })
export const post = (url, data) => request(url, { method: 'POST', data })
export const put = (url, data) => request(url, { method: 'PUT', data })
export const del = (url, data) => request(url, { method: 'DELETE', data })

export default request
