import requests

# 1. 填入你新买的 API Key (通常是 sk- 开头的纯英数字符串)
API_KEY = "sk-XW93aq6TLKgjrZILE05a4fB144A2498296Eb529c098b148a"

# 2. 根据截图填写的完整对话地址
URL = "https://dpapi.cn/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": "你好，这是一条接口连通性测试消息。如果你能正常接收，请简短地回复我。"}
    ],
    "max_tokens": 50
}

try:
    print("正在向 dpapi.cn 发送测试请求，请稍候...")
    response = requests.post(URL, headers=headers, json=data, timeout=10)

    if response.status_code == 200:
        print("\n✅ 连接成功！接口返回了数据：")
        print(response.json()['choices'][0]['message']['content'])
    else:
        print(f"\n❌ 请求失败，HTTP 状态码：{response.status_code}")
        print("详细错误信息：", response.text)

except requests.exceptions.RequestException as e:
    print("\n⚠️ 网络请求出现异常，请检查网络连接：")
    print(e)