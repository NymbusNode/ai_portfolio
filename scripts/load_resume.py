import asyncio
import os
import tiktoken
import openai
from pathlib import Path
from app.db import Base
from app.models import ResumeChunk
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# Determine if we're running directly or in Docker
import platform
import socket

# Try to resolve 'db' - if it works, we're in Docker
try:
    socket.gethostbyname('db')
    host = 'db'
except socket.gaierror:
    host = 'localhost'

# Use the appropriate host
DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@{host}:5432/portfolio_ai"

# Create the engine with a longer timeout
db_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Show SQL queries for debugging
    connect_args={"timeout": 30}  # Longer connection timeout
)
db_session = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

PROJ_ROOT_DIR = Path(__file__).parent.parent

# Set up OpenAI API
openai.api_key = settings.openai_api_key
enc = tiktoken.get_encoding("cl100k_base")

def test_chunk_text():
    """Test the chunk_text function with a sample text."""
    sample_text = "This is a test sentence. " * 10  # Repeat to create a longer text
    chunks = chunk_text(sample_text, chunk_size=50)
    print(f"Number of chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk[:50]}...")  # Print first 50 characters of each chunk

def chunk_text(text: str, chunk_size=200):
    """Split text into chunks of approximately chunk_size tokens."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(enc.encode(word))
        if current_size + word_size > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

async def main():
    # Create tables if they don't exist
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check for resume.txt first
    resume_file = PROJ_ROOT_DIR / "static" / "pdf" / "resume.txt"
    print(f"Looking for resume file at {resume_file}")
    # If not found, try creating a basic one
    if not resume_file.exists():
        print(f"Resume file not found at {resume_file}. Creating a sample file.")
        resume_text = """
        DJ Brown - Software Engineer & AI Developer
        
        EXPERIENCE
        Senior Software Engineer, AI Systems
        2023-Present
        - Developed RAG-based portfolio AI assistant using FastAPI, pydantic-ai, and PostgreSQL
        - Implemented streaming responses and tool-calling capabilities
        - Optimized vector search for quick context retrieval
        
        Software Engineer, Full Stack
        2020-2023
        - Built scalable applications using Python, JavaScript, and cloud services
        - Led development of internal tools that increased team productivity
        
        SKILLS
        Python, TypeScript, FastAPI, SQLAlchemy, PostgreSQL, Docker, gRPC, OpenAI API
        """
        
        # Create directory if needed
        resume_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write sample text
        with open(resume_file, "w") as f:
            f.write(resume_text)
    
    # Read the resume file
    resume_text = resume_file.read_text()
    print(f"Resume text length: {len(resume_text)} characters")
    # Create chunks
    chunks = chunk_text(resume_text)
    print(f"Split resume into {len(chunks)} chunks")
    
    # Generate embeddings and store in database
    async with db_session() as session:
        # Clear existing chunks
        await session.execute("TRUNCATE TABLE resume_chunks")
        await session.commit()
        
        # Create new chunks with embeddings
        for chunk_text in chunks:
            try:
                embedding_response = await openai.embeddings.create(
                    model=settings.embed_model,
                    input=chunk_text
                )
                embedding = embedding_response.data[0].embedding
                
                chunk = ResumeChunk(text=chunk_text, embedding=embedding)
                session.add(chunk)
                print(f"Added chunk: {chunk_text[:50]}...")
            except Exception as e:
                print(f"Error generating embedding: {e}")
        
        await session.commit()
        print("Resume chunks loaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
    #test_chunk_text()  # Run the test function to validate chunking