
import os
import uuid
import time
from typing import List
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import (verify_token, verify_user, verify_admin, create_access_token, 
                 get_user_from_token)
from tasks import run_reindex_background
from feedback_db import save_feedback, get_feedbacks
from user_db import (create_user, authenticate_user, get_user_by_username, 
                    update_user_profile, create_chat_session, get_user_chat_sessions,
                    save_chat_message, get_chat_messages, update_message_feedback,
                    delete_chat_session, update_session_title)
from typing import List
from models import (AskRequest, AskResponse, UploadResponse, ReindexResponse, 
                   FeedbackRequest, SourceItem, DevTokenRequest, UserRegistrationRequest,
                   UserLoginRequest, UserLoginResponse, UserProfileUpdateRequest,
                   UserProfileResponse, ChatSessionCreateRequest, ChatSessionResponse,
                   ChatMessageResponse, ChatSessionDetailResponse, ChatSessionUpdateRequest,
                   MessageFeedbackRequest)
from utils import detect_language
from store import store
from llm import generate_answer
from config import DATA_DIR, MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS, TOP_K_DEFAULT, AZURE_OPENID_CONFIG, JWT_SECRET,LLM_BACKEND, EMBED_BACKEND, VECTOR_STORE
from fastapi import Query
from datetime import datetime


logger = logging.getLogger("uvicorn")
app = FastAPI(title="RAG Backend - secure")

# Add HTTPBearer security scheme for Swagger UI (OpenAPI)
bearer_scheme = HTTPBearer()

# CORS (set via env var). default allow localhost:3000
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["*"])

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        claims = verify_token(token)
        return claims
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Get full user data from token"""
    token = credentials.credentials
    user_data = get_user_from_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_data

def get_is_user(claims: dict = Depends(get_current_user)) -> bool:
    role_user = verify_user(claims)
    print("[AUTH] User role: ", role_user)
    return role_user

def get_is_admin(claims: dict = Depends(get_current_user)) -> bool:
    role_admin = False
    role_admin = verify_admin(claims)
    print("[AUTH] Admin role: ", role_admin)
    return role_admin

@app.get("/health")
def health():
    return {"status": "ok", "llm_backend": LLM_BACKEND, "embedding" : EMBED_BACKEND }

# User Authentication Endpoints
@app.post("/auth/register", response_model=UserLoginResponse)
def register_user(user_data: UserRegistrationRequest):
    """Register a new user"""
    # Check if username or email already exists
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    success = create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        preferred_name=user_data.preferred_name,
        role=user_data.role,
        organization=user_data.organization,
        is_admin=(user_data.role == "admin")
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create user")
    
    # Authenticate and return token
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=500, detail="User created but authentication failed")
    
    token = create_access_token(user)
    return UserLoginResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )

@app.post("/auth/login", response_model=UserLoginResponse)
def login_user(login_data: UserLoginRequest):
    """Login user with username and password"""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = create_access_token(user)
    return UserLoginResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )

@app.get("/auth/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user_data)):
    """Get current user profile"""
    # Get full user data from database to ensure all fields are present
    full_user_data = get_user_by_username(current_user["username"])
    if not full_user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfileResponse(**full_user_data)

@app.put("/auth/profile", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_user_data)
):
    """Update user profile"""
    updates = profile_data.dict(exclude_unset=True)
    
    if updates:
        success = update_user_profile(current_user["id"], **updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update profile")
    
    # Get updated user data
    updated_user = get_user_by_username(current_user["username"])
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(**updated_user)

from fastapi import Body

@app.post("/dev/token")
def dev_token(req: DevTokenRequest):
    """
    Development helper - issue HS256 token. Only available when AZURE_TENANT not set
    """
    from jose import jwt
    from config import AZURE_TENANT, JWT_SECRET
    if AZURE_TENANT:
        raise HTTPException(status_code=403, detail="Dev token disabled when AZURE_TENANT is set")
    if req.username == "admin":
        payload = {"sub": req.username, "preferred_username": req.username, "roles": ["user", "admin"]}
    else:
        payload = {"sub": req.username, "preferred_username": req.username, "roles": ["user"]}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/reindex", response_model=ReindexResponse)
def reindex(folder: str = "", background_tasks: BackgroundTasks = None, user=Depends(get_current_user), is_admin: bool = Depends(get_is_admin)):
    if is_admin:
        base = Path(folder).resolve() if folder else Path(DATA_DIR)
        if background_tasks is not None:
            background_tasks.add_task(run_reindex_background, base)
            return ReindexResponse(folder=str(base), chunks_indexed=-1)
        count = store.build_from_folder(base)
        return ReindexResponse(folder=str(base), chunks_indexed=count)
    else:
        raise HTTPException(status_code=403, detail="Admin privileges required")

@app.post("/upload", response_model=List[UploadResponse])
async def upload(files: List[UploadFile] = File(...), user=Depends(get_current_user), is_admin: bool = Depends(get_is_admin)):
    if is_admin:
        results = []
        filesToProcess = []
        filenames = []
        added=0
        upload_dir = Path(DATA_DIR) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            filename = Path(f.filename).name
            ext = filename.split(".")[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")
            content = await f.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=413, detail="File too large")
            dest = upload_dir / filename
            filenames.append(filename)
            if VECTOR_STORE == "faiss" :
                if dest.exists():
                    dest = upload_dir / f"{dest.stem}-{uuid.uuid4().hex}{dest.suffix}"
                dest.write_bytes(content)
                filesToProcess.append(str(dest))
            elif VECTOR_STORE == "pinecone":
                if store.file_already_indexed(filename):
                    print("Skipping already indexed file:", filename)
                    if os.path.exists(dest):
                        os.remove(dest)  # delete uploaded file if already indexed
                    continue
                dest.write_bytes(content)  
                filesToProcess.append(str(dest))
        if filesToProcess:
            added = store.append_files(filesToProcess)
        results.append(UploadResponse(file=str(filenames), chunks_added=added if added else 0))
        return results
    else:
        raise HTTPException(status_code=403, detail="Admin privileges required")

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, current_user: dict = Depends(get_current_user_data), is_user: bool = Depends(get_is_user)):
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
        
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    
    # Initialize timing measurements
    timings = {}
    
    # Step 0: Language detection
    start_time = time.perf_counter()
    q_lang = detect_language(req.query)
    timings["language_detection_ms"] = round((time.perf_counter() - start_time) * 1000, 4)
    print("[DETECT]", q_lang, req.query)
    
    # Steps 1 & 2: Embedding generation and vector search (measured in store.py)
    hits, search_timings = store.search(req.query, k=req.top_k or TOP_K_DEFAULT)
    timings.update(search_timings)  # Add embedding_ms and vector_search_ms
    
    # Initialize answer and sources
    answer = ""
    sources = []
    
    if not hits:
        print("[ASK] No relevant context found.")
        timings["llm_generation_ms"] = 0
        answer = "I couldn't find relevant information in the knowledge base to answer your question."
    else:
        snippets = [h["text"] for h in hits]
        sources = [SourceItem(file=h["file"], chunk_id=h["chunk_id"], score=h["score"], 
                             score_normalized=h["score_normalized"], preview=h["text"]) for h in hits]
        
        # Step 3: LLM generation (measured in llm.py)
        if req.use_synthesis:
            answer, llm_timings = generate_answer(req.query, snippets, q_lang, response_length=req.response_length)
            timings.update(llm_timings)  # Add llm_generation_ms
        else:
            answer = None
            timings["llm_generation_ms"] = 0
        
        if not answer:
            print("[ASK] LLM backend disabled or generation failed; providing context-based response.")
            # Instead of returning raw snippet, provide a more helpful response
            answer = f"Based on the documents, here is the most relevant information I found:\n\n{snippets[0]}"
            if "llm_generation_ms" not in timings:
                timings["llm_generation_ms"] = 0  # No actual LLM call made

    # Update sources to include page_number from Pinecone integration
    sources = [SourceItem(file=h["file"], chunk_id=h["chunk_id"], score=h["score"], 
                         score_normalized=h["score_normalized"], preview=h["text"], 
                         page_number=h.get("page_number", -1)) for h in hits]
    
    # Calculate total time with all separated components
    timings["total_ms"] = round(sum([
        timings["language_detection_ms"],
        timings["embedding_ms"],
        timings["vector_search_ms"], 
        timings["llm_generation_ms"]
    ]), 4)
    
    # Save to chat session if session_id is provided
    if req.session_id:
        try:
            # Save user message
            save_chat_message(
                session_id=req.session_id,
                user_id=current_user["id"],
                message_type="user",
                content=req.query
            )
            
            # Save assistant response
            save_chat_message(
                session_id=req.session_id,
                user_id=current_user["id"],
                message_type="assistant",
                content=answer,
                sources=[source.dict() for source in sources]
            )
        except Exception as e:
            print(f"[ERROR] Failed to save chat messages: {e}")
            # Don't fail the request if chat saving fails
    
    # Also save to legacy history system for backward compatibility
    session_id = req.session_id or "anon"
    history_dir = Path(DATA_DIR) / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    hist_file = history_dir / f"{session_id}.json"
    import json
    hist = []
    if hist_file.exists():
        try:
            hist = json.loads(hist_file.read_text(encoding="utf-8"))
        except Exception:
            hist = []
    hist.append({
        "query": req.query, 
        "answer": answer, 
        "timings": timings,
        "timestamp": time.time(),
        "sources_count": len(sources)
    })
    hist_file.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Log detailed timing information with updated naming
    print(f"[TIMING] Language: {timings['language_detection_ms']}ms, "
          f"Embedding: {timings['embedding_ms']}ms, "
          f"Vector Search: {timings['vector_search_ms']}ms, "
          f"LLM: {timings['llm_generation_ms']}ms, "
          f"Total: {timings['total_ms']}ms")
    
    return AskResponse(query=req.query, language=q_lang, answer=answer or "", sources=sources, session_id=req.session_id)

@app.post("/feedback")
def feedback(req: FeedbackRequest, user=Depends(get_current_user), is_user: bool = Depends(get_is_user)):
    if is_user:
        # persist feedback to sqlite via feedback_db.save_feedback
        uname = user.get("preferred_username", "anonymous")
        save_feedback(uname, req.session_id, req.query, None, req.rating, req.comment)
        return JSONResponse({"status":"ok"})
    else:
        raise HTTPException(status_code=403, detail="User privileges required")

@app.get("/feedbacks")
def list_feedbacks(limit: int = Query(1000, ge=1, le=10000), user=Depends(get_current_user), is_admin: bool = Depends(get_is_admin)):
    """
    Retrieve recent feedback records for analysis.
    """
    if is_admin:
        return get_feedbacks(limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Admin privileges required")

# Chat Session Management Endpoints
@app.post("/chat/sessions", response_model=ChatSessionResponse)
def create_new_chat_session(
    session_data: ChatSessionCreateRequest,
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Create a new chat session"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    session_id = create_chat_session(current_user["id"], session_data.title)
    
    # Return the created session
    sessions = get_user_chat_sessions(current_user["id"])
    created_session = next((s for s in sessions if s["id"] == session_id), None)
    
    if not created_session:
        raise HTTPException(status_code=500, detail="Failed to create chat session")
    
    return ChatSessionResponse(**created_session)

@app.get("/chat/sessions", response_model=List[ChatSessionResponse])
def get_chat_sessions(
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Get all chat sessions for current user"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    sessions = get_user_chat_sessions(current_user["id"])
    return [ChatSessionResponse(**session) for session in sessions]

@app.get("/chat/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_chat_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Get detailed chat session with messages"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    # Get session info
    sessions = get_user_chat_sessions(current_user["id"])
    session = next((s for s in sessions if s["id"] == session_id), None)
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Get messages
    messages = get_chat_messages(session_id, current_user["id"])
    
    return ChatSessionDetailResponse(
        session=ChatSessionResponse(**session),
        messages=[ChatMessageResponse(**msg) for msg in messages]
    )

@app.put("/chat/sessions/{session_id}")
def update_chat_session(
    session_id: str,
    session_data: ChatSessionUpdateRequest,
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Update chat session title"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    success = update_session_title(session_id, current_user["id"], session_data.title)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found or update failed")
    
    return {"status": "ok"}

@app.delete("/chat/sessions/{session_id}")
def delete_chat_session_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Delete chat session"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    success = delete_chat_session(session_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found or delete failed")
    
    return {"status": "ok"}

@app.post("/chat/feedback")
def submit_message_feedback(
    feedback_data: MessageFeedbackRequest,
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Submit feedback for a specific message"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    success = update_message_feedback(
        feedback_data.message_id,
        current_user["id"],
        feedback_data.rating,
        feedback_data.comment
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or feedback update failed")
    
    # Also save to feedback table for analytics (get message details first)
    try:
        from user_db import get_message_details
        message_details = get_message_details(feedback_data.message_id, current_user["id"])
        if message_details:
            # Create a session ID that indicates this is chat feedback
            chat_session_id = f"chat_message_{feedback_data.message_id}"
            save_feedback(
                user=current_user.get("preferred_username", current_user.get("username", "anonymous")),
                session_id=chat_session_id,
                query=message_details.get("content", "Chat feedback"),
                source_chunk=None,
                rating=feedback_data.rating,
                comment=feedback_data.comment or ""
            )
    except Exception as e:
        print(f"[WARNING] Failed to save chat feedback to feedback table: {e}")
        # Don't fail the request if this fails
    
    return {"status": "ok"}

@app.get("/user/stats")
def get_user_statistics(
    current_user: dict = Depends(get_current_user_data),
    is_user: bool = Depends(get_is_user)
):
    """Get user activity statistics"""
    if not is_user:
        raise HTTPException(status_code=403, detail="User privileges required")
    
    try:
        from user_db import get_user_statistics
        stats = get_user_statistics(current_user["id"])
        return stats
    except Exception as e:
        print(f"[ERROR] Failed to get user stats: {e}")
        # Return default stats if there's an error
        return {
            "total_chats": 0,
            "total_messages": 0,
            "feedback_given": 0,
            "documents_viewed": 0,
            "recent_activity": []
        }

