import logging
import openai
from anthropic import AsyncAnthropic
import anthropic
from pydantic_ai import Agent, Tool
from sqlalchemy import text as sql
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.db import async_session
from fastapi import Depends
from app.config import settings
from app.utils import load_file_text
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pathlib import Path
import asyncio
PROJ_ROOT_DIR = Path(__file__).parent.parent.parent
BACKUP_INSTRUCTIONS = (
    "You are DJ Brown's professional assistant. Use the provided context chunks "
    "to answer professionally and highlight achievements quantitatively. "
    "If you call a tool, only call it with correct JSON."
)

class AgentManager:
    logger = logging.getLogger(__name__)

    def __init__(self, llm: str = "gpt-4o"):
        """Initialize the agent manager with an OpenAI model and default settings."""
        self.llm = llm
        self.chatHistory = []
        self.tools = []
        self.initAgent()

    def initAgent(self) -> Agent:
        """Initialize the agent with OpenAI model and instructions."""
        model = self.getModel()
        instructions = self.getInstructions() 
        self.agent = Agent(
            model,
            instructions=instructions,
        )
        self.logger.info(f"Initialized agent with model: {self.llm}")
        return self.agent
    
    def getModel(self, llm: str = None) -> OpenAIModel:
        """Initialize and return the OpenAI model."""
        llm = llm or self.llm
        self.model = OpenAIModel(llm, provider=OpenAIProvider(api_key=settings.openai_api_key))
        return self.model
    
    def getInstructions(self) -> str:
        """Load custom instructions for the agent."""
        self.instructions = load_file_text(PROJ_ROOT_DIR / "app" / "files" / "base_instructions.txt")
        if not self.instructions:
            self.instructions = BACKUP_INSTRUCTIONS
        self.logger.info(f"Using instructions: {self.instructions[:25]}...")  # Log first 25 chars
        return self.instructions

async def test_async():
    agentMgr = AgentManager()
    agent = agentMgr.agent if hasattr(agentMgr, 'agent') else agentMgr.initAgent()
    async with agent.run_stream('Hi how are you') as result:
        async for message in result.stream_text(delta=True):
            print(message)

if __name__ == "__main__":
    pass
    #asyncio.run(test_async())
    #print(result.output)
'''
class PortfolioAgent(Agent):
    system = SYSTEM
    tools = TOOLS  

    async def astream(self, question: str):
        try:
            # For OpenAI models
            if settings.default_model.startswith("gpt"):
                stream = openai.chat.completions.create(
                    model=settings.default_model,
                    messages=[
                        {"role": "system", "content": self.system},
                        {"role": "user", "content": f"Question: {question}"}
                    ],
                    #tools=self.tools,
                    stream=True  # Enable streaming
                )
                
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            # For Claude models
            else:
                with anthropic_client.messages.stream(
                    model=settings.default_model,
                    system=self.system,
                    messages=[{"role": "user", "content": f"Question: {question}"}],
                    #tools=self.tools,
                    max_tokens=1024
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
        except Exception as e:
            print(f"Error in astream: {e}")
            yield f"I'm having trouble accessing my knowledge base at the moment. Error: {str(e)}"
'''