import requests
import json


def main():
    url = "https://apihub.agnes-ai.com/v1/chat/completions"

    payload = json.dumps({
        "model": "agnes-2.0-flash",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "你好"
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-g7Jn2whWMTeAO4ocaPppyC0eftaC4c6hW6m46GTdT5SXuGGr'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


if __name__ == '__main__':
    main()
