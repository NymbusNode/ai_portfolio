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

openai.api_key = settings.openai_api_key
anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# ------- tools the model can call -------
class LatestProject(Tool):
    """Return the title and one-sentence summary of my most recent side-project."""

    async def run(self) -> str:
        projects = {
            "AI Portfolio": "A professional portfolio with an AI chatbot assistant that can answer questions about my experience and projects",
            "Nymbus AI": "A crypto assistant with wallet integrations and LLM Q&A for 200+ chains",
            "Mini Reconciler": "Internal finance reconciliation tool that cut manual operations by 80%"
        }
        # Return the first project as the most recent one
        project = list(projects.items())[0]
        return f"{project[0]} — {project[1]}."

TOOLS = [LatestProject]

SYSTEM = (
    "You are DJ Brown's professional assistant. Use the provided context chunks "
    "to answer professionally and highlight achievements quantitatively. "
    "If you call a tool, only call it with correct JSON."
)

class PortfolioAgent(Agent):
    system = SYSTEM
    tools = TOOLS  # optional

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text"""
        try:
            # Use the client without await - the method returns the embedding directly
            resp = openai.embeddings.create(model=settings.embed_model, input=text)
            return resp.data[0].embedding
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Return a zero vector as fallback
            return [0.0] * 768

    async def fetch_context(self, question: str) -> str:
        """Retrieve relevant context from resume chunks"""
        try:
            query_embedding = self.embed(question)  # Remove await
            
            async with async_session() as session:
                # Perform vector similarity search using dot product
                query = """
                SELECT text, embedding <=> :embedding AS distance
                FROM resume_chunks
                ORDER BY distance ASC
                LIMIT 5
                """
                result = await session.execute(
                    sql(query),
                    {"embedding": query_embedding}
                )
                chunks = result.all()
                
                if not chunks:
                    return "No relevant information found."
                    
                return "\n".join(chunk[0] for chunk in chunks)
        except Exception as e:
            print(f"Error fetching context: {e}")

            #return f"Error accessing knowledge base: {str(e)}"

    async def llm(self, messages):
        """Send messages to the selected LLM provider"""
        if settings.default_model.startswith("gpt"):
            response = await openai.chat.completions.create(
                model=settings.default_model,
                messages=messages,
                tools=self.tools
            )
            return {
                "role": "assistant",
                "content": response.choices[0].message.content or "",
                "tool_calls": response.choices[0].message.tool_calls
            }
        else:
            response = await anthropic_client.messages.create(
                model=settings.default_model,
                system=self.system,
                messages=messages,
                max_tokens=1024,
                tools=self.tools
            )
            return {
                "role": "assistant", 
                "content": response.content[0].text
                # Add Claude specific tool call handling if needed
            }

    async def astream(self, question: str):
        """Stream tokens from the LLM response."""
        try:
            context = await self.fetch_context(question)
        except Exception as e:
            print(f"Error fetching context: {e}")
            context = "No relevant context found."
        try:
            # For OpenAI models
            if settings.default_model.startswith("gpt"):
                stream = await openai.chat.completions.create(
                    model=settings.default_model,
                    messages=[
                        {"role": "system", "content": self.system},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                    ],
                    tools=self.tools,
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
                    messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
                    tools=self.tools,
                    max_tokens=1024
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
        except Exception as e:
            print(f"Error in astream: {e}")
            yield f"I'm having trouble accessing my knowledge base at the moment. Error: {str(e)}"

    async def run_async(self, user: str, context: str = None) -> str:
        """Execute the agent with tool-calling capability."""
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user}"}
        ]
        
        while True:
            response = await self.llm(messages)
            messages.append(response)
            
            # Check if the model wants to call a tool
            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                return response["content"]
                
            # Process each tool call
            for tool_call in tool_calls:
                # Handle OpenAI's tool call format
                if "function" in tool_call:
                    tool_name = tool_call["function"]["name"]
                    try:
                        # Find the tool by name
                        tool_class = next(t for t in self.tools if t.__name__ == tool_name)
                        tool = tool_class()
                        # Execute the tool
                        result = await tool.run()
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool", 
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": result
                        })
                    except Exception as e:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": f"Error: {str(e)}"
                        })
                        
            # Get final response after tool use
            if tool_calls:
                continue
            else:
                return response["content"]

    @property
    def tool_schema(self):
        """Convert Pydantic tools to OpenAI tools format"""
        tools = []
        for tool_cls in self.tools:
            tool = tool_cls()
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_cls.__name__,
                    "description": tool.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            })
        return tools