from pydantic_ai import Agent

SYSTEM_PROMPT = (
    "You are Daryck (DJ) Brown’s professional assistant and career advocate. "
    "Answer accurately from the provided resume and project data, highlight "
    "achievements, and keep the tone confident and friendly."
)

class PortfolioAgent(Agent):
    # pydantic-ai ≥0.2.x: declare the system prompt like so
    system = SYSTEM_PROMPT

    async def fetch_context(self, question: str):
        # TODO: embed question and query pgvector for relevant chunks
        return "(context goes here)"

    async def chat(self, question: str) -> str:
        context = await self.fetch_context(question)
        # .run_async is the new entry-point
        return await self.run_async(user=question, context=context)