import requests
import json

url = "http://127.0.0.1:8000/api/audit"

payload = {
    "text": "Paul Ekman — “Basic Emotions”（论文/PDF，Ekman 对基本情绪理论的阐述与证据综述）。Ekman 的研究长期被引用，讨论了愤怒、厌恶、恐惧、快乐（喜悦）、悲伤、惊讶等“基本情绪”，并指出 蔑视（contempt） 有强证据成为第七种。"
}

try:
    print("正在发送请求...")
    response = requests.post(url, json=payload)

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        print("\n=== 审计结果 ===")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print("出错啦:", response.text)

except Exception as e:
    print(f"连接失败: {e}")