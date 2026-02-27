/**
 * 宠物状态管理 Composable
 * 负责管理宠物的状态、情绪和交互
 */

import { ref, computed } from 'vue'

// 默认配置
const defaultConfig = {
  name: '小助手',
  level: 1,
  exp: 0,
  mood: 'normal',
  state: 'idle'
}

// 状态管理
const petConfig = ref({ ...defaultConfig })
const customSvg = ref('')
const animationConfig = ref({})

// 从本地存储加载
const loadPetConfig = () => {
  try {
    const saved = uni.getStorageSync('petConfig')
    if (saved) {
      petConfig.value = { ...defaultConfig, ...saved }
    }
    
    // 加载自定义SVG
    const savedSvg = uni.getStorageSync('petCustomSvg')
    if (savedSvg) {
      customSvg.value = savedSvg
    }
    
    // 加载动画配置
    const savedAnim = uni.getStorageSync('petAnimationConfig')
    if (savedAnim) {
      try {
        animationConfig.value = typeof savedAnim === 'string' ? JSON.parse(savedAnim) : savedAnim
      } catch (e) {
        console.warn('解析动画配置失败:', e)
      }
    }
  } catch (e) {
    console.warn('加载宠物配置失败:', e)
  }
}

// 从服务器加载自定义配置
const loadCustomizationFromServer = () => {
  const userInfo = uni.getStorageSync('userInfo')
  if (!userInfo || !userInfo.id) {
    return Promise.resolve()
  }

  const API_BASE = `http://101.35.132.175:5000`
  
  return new Promise((resolve) => {
    uni.request({
      url: `${API_BASE}/api/pet/customization`,
      method: 'GET',
      data: { user_id: userInfo.id },
      success: (res) => {
        if (res.data.code === 200 && res.data.data) {
          const data = res.data.data
          customSvg.value = data.svg_content || ''
          if (data.animation_config) {
            try {
              animationConfig.value = typeof data.animation_config === 'string' 
                ? JSON.parse(data.animation_config) 
                : data.animation_config
            } catch (e) {
              console.warn('解析动画配置失败:', e)
            }
          }
          // 保存到本地
          if (customSvg.value) {
            uni.setStorageSync('petCustomSvg', customSvg.value)
          }
          if (Object.keys(animationConfig.value).length > 0) {
            uni.setStorageSync('petAnimationConfig', JSON.stringify(animationConfig.value))
          }
        }
        resolve()
      },
      fail: () => {
        console.warn('加载自定义配置失败')
        resolve()
      }
    })
  })
}

// 保存到本地存储
const savePetConfig = () => {
  try {
    uni.setStorageSync('petConfig', petConfig.value)
  } catch (e) {
    console.warn('保存宠物配置失败:', e)
  }
}

// 计算属性
const expToNextLevel = computed(() => {
  return petConfig.value.level * 100 // 每级需要 等级 * 100 经验
})

const expProgress = computed(() => {
  return (petConfig.value.exp / expToNextLevel.value) * 100
})

// 添加经验值
const addExp = (amount) => {
  petConfig.value.exp += amount
  const needed = expToNextLevel.value
  
  if (petConfig.value.exp >= needed) {
    // 升级
    petConfig.value.exp -= needed
    petConfig.value.level += 1
    triggerState('celebrating', 3000)
    uni.showToast({ title: `${petConfig.value.name} 升级了！`, icon: 'none' })
  }
  
  savePetConfig()
}

// 触发状态（临时状态，会自动恢复）
let stateTimer = null
const triggerState = (state, duration = 2000) => {
  const originalState = petConfig.value.state
  petConfig.value.state = state
  
  if (stateTimer) {
    clearTimeout(stateTimer)
  }
  
  stateTimer = setTimeout(() => {
    petConfig.value.state = originalState
    stateTimer = null
  }, duration)
}

// 响应应用事件
const onTaskCompleted = () => {
  addExp(10)
  triggerState('happy', 2000)
  petConfig.value.mood = 'excited'
  savePetConfig()
}

const onPlanCreated = () => {
  addExp(5)
  triggerState('happy', 1500)
  savePetConfig()
}

const onPlanArchived = () => {
  addExp(20)
  triggerState('celebrating', 3000)
  petConfig.value.mood = 'excited'
  savePetConfig()
}

const onVocabLearned = () => {
  addExp(3)
  triggerState('happy', 1000)
  savePetConfig()
}

// 初始化
loadPetConfig()

// 初始化时从服务器加载
loadCustomizationFromServer()

export function usePet() {
  return {
    // 状态
    petConfig: computed(() => petConfig.value),
    customSvg: computed(() => customSvg.value),
    animationConfig: computed(() => animationConfig.value),
    expToNextLevel,
    expProgress,
    
    // 方法
    addExp,
    triggerState,
    setMood: (mood) => {
      petConfig.value.mood = mood
      savePetConfig()
    },
    setName: (name) => {
      petConfig.value.name = name
      savePetConfig()
    },
    setCustomSvg: (svg) => {
      customSvg.value = svg
      uni.setStorageSync('petCustomSvg', svg)
    },
    setAnimationConfig: (config) => {
      animationConfig.value = config
      uni.setStorageSync('petAnimationConfig', JSON.stringify(config))
    },
    reloadCustomization: loadCustomizationFromServer,
    
    // 事件响应
    onTaskCompleted,
    onPlanCreated,
    onPlanArchived,
    onVocabLearned,
  }
}
