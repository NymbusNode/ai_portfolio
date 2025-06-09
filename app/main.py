from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
from .schemas import ChatRequest, ChatResponse
from .chat.agent import PortfolioAgent

app = FastAPI(title="Portfolio AI")

templates = Jinja2Templates(directory="templates")
agent = PortfolioAgent()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(req: ChatRequest):
    answer = await agent.chat(req.message)
    return ChatResponse(answer=answer)

@app.get("/chat/stream")
async def chat_stream(message: str):
    async def event_generator():
        answer = await agent.chat(message)
        for token in answer.split():
            yield f"data: {token} \n\n"
            await asyncio.sleep(0.05)
    return StreamingResponse(event_generator(), media_type="text/event-stream")