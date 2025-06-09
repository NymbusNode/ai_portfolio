from pydantic_ai import Agent, Prompt, Message
from pathlib import Path

SYSTEM_PROMPT = (
    "You are Daryck(aka DJ) Brown’s professional assistant and career advocate. Answer accurately "
    "from the provided resume and project data, highlight achievements, "
    "keep tone confident and friendly."
)

class PortfolioAgent(Agent):
    prompt = Prompt(system=SYSTEM_PROMPT)

    async def fetch_context(self, question: str):
        # TODO: embed question and query pgvector for top chunks
        return "(context goes here)"

    async def chat(self, question: str) -> str:
        context = await self.fetch_context(question)
        response = await self.prompt.run_async(user=question, context=context)
        return response