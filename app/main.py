from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
from .schemas import ChatRequest, ChatResponse
from .chat.agent import AgentManager
from app.config import settings
import json

app = FastAPI(title="Portfolio AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

agentMgr = AgentManager()
agent = agentMgr.agent if hasattr(agentMgr, 'agent') else agentMgr.initAgent()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(
    message: str = Form(...),
    model: str = Form(None),
    request: Request = None,
):
    #TODO:FEtoBE comm issue- not getting message argument, and not return response to UI
    #First check frontend and then check the implementation of EventSourceResponse object, and yield, 
    # EventSourceResponse may not be needed
    print(f"Received message: {message}\n model: {model}\n request: {request}")
    if model:
        settings.default_model = model
    print(f"Received message: {message} with model: {settings.default_model}")

    def test_generator():
        print(f"test_generator called with message: {message}")
        response= ['this is', 'a test message,', 'for the', 'user message:',f'{message}']
        for msg in response:
            print(f"Yielding message: {msg}")
            sleep_time = 0.2  # Simulate processing time
            yield f"data: {json.dumps({'event': 'message', 'data': msg})}\n\n"


    async def event_generator():
       print(f"user message: {message}")
       try:
           async with agent.run_stream(user_prompt=message) as response:
               async for chunk in response.stream_text(delta=True):
                   print(f"Streaming message: {chunk}")
                   payload = {"data": chunk}
                   # yield a proper SSE "data:" line
                   yield f"data: {json.dumps(payload)}\n\n"
                   # let the event loop breathe
                   await asyncio.sleep(0)
       except Exception as e:
           print(f"Error in chat stream: {e}")
           # SSE error event (optional)
           yield f"event: error\ndata: {str(e)}\n\n"

   # Use StreamingResponse directly:
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


'''
@app.get("/chat/stream")
async def chat_stream(message: str):
    async def event_generator():
        answer = await agent.chat(message)
        for token in answer.split():
            yield json.dumps({"event": "message", "data": token})
            await asyncio.sleep(0.05)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
'''