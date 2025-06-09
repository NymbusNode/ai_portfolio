import asyncio
import uuid
import grpc
from app.chat.proto import chat_pb2, chat_pb2_grpc
from .agent import PortfolioAgent

a = PortfolioAgent()

class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    async def StreamChat(self, request_iterator, context):
        async for msg in request_iterator:
            if msg.role == "user":
                answer = await a.chat(msg.content)
                yield chat_pb2.ChatMessage(
                    id=str(uuid.uuid4()), content=answer, role="assistant"
                )

async def serve():
    server = grpc.aio.server()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())