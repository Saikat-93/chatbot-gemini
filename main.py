from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from google.genai import types
from mem0 import Memory
from dotenv import load_dotenv
import logging
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="chat_bot")

app.mount("/static", StaticFiles(directory="."), name="static")

# --- Gemini client ---
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Mem0 config ---
mem_config = {
    "llm": {
        "provider": "gemini",
        "config": {
            "model": "gemini-2.5-flash",
            "api_key": os.getenv("GEMINI_API_KEY"),
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "multi-qa-MiniLM-L6-cos-v1"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "chat_memory",
            "embedding_model_dims": 384,
            "path": "./qdrant_storage"
        }
    }
}

try:
    memory = Memory.from_config(mem_config)
    logger.info("✅ Mem0 initialized successfully")
except Exception as e:
    logger.error(f"❌ Mem0 init failed: {e}")
    memory = None

MODEL = "gemini-2.5-flash"


# --- Schemas ---
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# --- Serve index.html ---
@app.get("/", response_class=FileResponse)
async def index():
    return FileResponse("index.html")


# --- Chat endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Try to get memories (won't crash if Mem0 fails)
    memory_context = ""
    if memory:
        try:
            memories = memory.search(req.message, user_id=req.session_id, limit=5)
            if memories and memories.get("results"):
                facts = [m["memory"] for m in memories["results"]]
                memory_context = "Relevant context from previous messages:\n" + "\n".join(f"- {f}" for f in facts)
                logger.info(f"📝 Found {len(facts)} memories for session {req.session_id}")
        except Exception as e:
            logger.error(f"❌ Mem0 search failed: {e}")

    system_prompt = (
        "You are a helpful assistant. Use the provided context to give personalized, coherent responses.\n\n"
        + memory_context
    ).strip()

    # Call Gemini
    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=req.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
            ),
        )
        reply = response.text
    except Exception as e:
        logger.error(f"❌ Gemini error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # Try to store memory (won't crash if Mem0 fails)
    if memory:
        try:
            memory.add(
                [
                    {"role": "user", "content": req.message},
                    {"role": "assistant", "content": reply},
                ],
                user_id=req.session_id,
            )
        except Exception as e:
            logger.error(f"❌ Mem0 add failed: {e}")

    return ChatResponse(reply=reply, session_id=req.session_id)


# --- Memory endpoints ---
@app.get("/memories/{session_id}")
async def get_memories(session_id: str):
    if not memory:
        return {"session_id": session_id, "memories": [], "error": "Mem0 not available"}
    result = memory.get_all(user_id=session_id)
    return {"session_id": session_id, "memories": result.get("results", [])}


@app.delete("/memories/{session_id}")
async def clear_memories(session_id: str):
    if not memory:
        return {"message": "Mem0 not available"}
    memory.delete_all(user_id=session_id)
    return {"message": f"Cleared memories for session {session_id}"}