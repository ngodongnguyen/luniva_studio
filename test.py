import httpx

BASE_URL = "http://localhost:8383/test/chat"
SENDER_ID = "test_user"


def chat(message: str) -> None:
    response = httpx.post(BASE_URL, json={"sender_id": SENDER_ID, "message": message})
    data = response.json()
    print(f"\n[{data['classification']}] intent={data['intent']}")
    print(f"Bot: {data['response']}")


if __name__ == "__main__":
    print("Luniva Studio Chatbot Test — gõ 'exit' để thoát\n")
    while True:
        try:
            message = input("Bạn: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not message:
            continue
        if message.lower() == "exit":
            break
        chat(message)
