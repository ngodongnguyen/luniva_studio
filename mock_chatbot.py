"""
Mock chatbot backend for testing.
Run: uvicorn mock_chatbot:app --port 9000
"""

from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/chat")
async def chat(request: Request) -> dict:
    body = await request.json()
    message = body.get("message", "")
    user_id = body.get("user_id", "unknown")
    print(f"[mock-chatbot] user_id={user_id} message={message!r}")
    return {"answer": f"Bạn vừa nói: {message}"}
