# llm.py (improved with bugfixes + logging)
from typing import List, Optional
from config import (
    LLM_BACKEND, OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_HOST, OLLAMA_MODEL,
    HF_MODEL, HF_MAX_NEW_TOKENS, HF_TEMPERATURE
)
import logging
logger = logging.getLogger(__name__)


def _wrap_prompt(query: str, snippets: List[str], lang_code: str, is_encoder_decoder: bool, response_length: int = 50) -> List[dict]:
    context = "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(snippets))
    
    # Map response length to descriptive terms
    if response_length <= 25:
        length_instruction = "Keep your answer concise and brief."
    elif response_length <= 50:
        length_instruction = "Provide a moderate length answer with key details."
    elif response_length <= 75:
        length_instruction = "Give a detailed answer with comprehensive information."
    else:
        length_instruction = "Provide a thorough and comprehensive answer with extensive details."

    if is_encoder_decoder:
        # Instruction style (T5/mT5/Marian/mBART)
        sys = (
            f"You are a document assistant that answers questions using the provided context. "
            f"RULES:\n"
            f"1. Primarily use information from the provided context below\n"
            f"2. For questions about the documents themselves (like 'what documents do you have' or 'tell me about your knowledge base'), you can describe and summarize the content you see\n"
            f"3. For specific factual questions, stick strictly to the context. If the context doesn't contain enough information, respond with: 'I don't have enough information in the provided documents to answer this question.'\n"
            f"4. Do NOT use general knowledge for specific facts not in the context\n"
            f"5. You may make reasonable inferences from the context when describing or summarizing document contents\n"
            f"6. Respond in the same language as the question, which is '{lang_code}'\n"
            f"7. {length_instruction}\n"
            f"8. Do NOT include citation markers like [1], [2] in your answer\n"
            f"9. If the context includes procedures or instructions, provide the complete steps\n"
        )
        user = f"Question: {query}\n\nContext from documents:\n{context}\n\nAnswer (using ONLY the context above):"
        return [{"role": "user", "content": sys + "\n" + user}]
    else:
        # Chat style (GPT, LLaMA, etc.)
        sys = (
            f"You are a document assistant that answers questions using the provided context. "
            f"RULES:\n"
            f"1. Primarily use information from the provided context below\n"
            f"2. For questions about the documents themselves (like 'what documents do you have' or 'tell me about your knowledge base'), you can describe and summarize the content you see\n"
            f"3. For specific factual questions, stick strictly to the context. If the context doesn't contain enough information, respond with: 'I don't have enough information in the provided documents to answer this question.'\n"
            f"4. Do NOT use general knowledge for specific facts not in the context\n"
            f"5. You may make reasonable inferences from the context when describing or summarizing document contents\n"
            f"6. Respond in the same language as the question, which is '{lang_code}'\n"
            f"7. {length_instruction}\n"
            f"8. Do NOT include citation markers like [1], [2] in your answer\n"
            f"9. If the context includes procedures or instructions, provide the complete steps\n"
        )
        user = f"Question: {query}\n\nContext from documents:\n{context}\n\nAnswer (using ONLY the context above):"
        return [{"role": "system", "content": sys}, {"role": "user", "content": user}]

def _is_meta_question(query: str) -> bool:
    """
    Check if the question is about the knowledge base itself or documents in general.
    These questions should be allowed more flexibility.
    """
    query_lower = query.lower()
    meta_keywords = [
        "tell me about the documents", "what documents", "knowledge base", "what's in",
        "summarize the documents", "overview of documents", "what information",
        "contents of", "available documents", "document summary", "what do you know",
        "what can you help", "what topics", "document topics", "files available"
    ]
    return any(keyword in query_lower for keyword in meta_keywords)

def _validate_context_usage(answer: str, snippets: List[str], query: str = "") -> bool:
    """
    Validate if the answer appears to use the provided context.
    Returns True if the answer seems to use context, False if it seems like general knowledge.
    """
    if not answer or not snippets:
        return False
    
    # Allow more flexibility for meta-questions about the knowledge base
    if _is_meta_question(query):
        return True
    
    # Check if answer indicates insufficient context
    insufficient_phrases = [
        "don't have enough information",
        "insufficient information", 
        "not enough information",
        "cannot find",
        "not mentioned",
        "not provided",
        "no information about",
        "context doesn't contain"
    ]
    
    answer_lower = answer.lower()
    if any(phrase in answer_lower for phrase in insufficient_phrases):
        return True  # This is a valid "insufficient context" response
    
    # Check if answer contains keywords from the context
    context_text = " ".join(snippets).lower()
    answer_words = set(answer_lower.split())
    context_words = set(context_text.split())
    
    # Remove common words for better matching
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    meaningful_answer_words = answer_words - common_words
    meaningful_context_words = context_words - common_words
    
    # Check overlap between answer and context (reduced threshold for more flexibility)
    if meaningful_answer_words:
        overlap = meaningful_answer_words & meaningful_context_words
        overlap_ratio = len(overlap) / len(meaningful_answer_words)
        return overlap_ratio >= 0.2  # Reduced from 0.3 to 0.2 for more flexibility
    
    return False

def generate_answer(query: str, snippets: List[str], lang_code: str, response_length: int = 50) -> tuple[Optional[str], dict]:
    """
    Generate an answer using the configured LLM backend.
    
    Returns:
        tuple: (answer, timings) where timings contains llm_generation_ms
    """
    import time
    
    start_time = time.perf_counter()
    
    if LLM_BACKEND == "none":
        timing = {"llm_generation_ms": 0.0}
        return None, timing

    # ---------------- OPENAI ----------------
    if LLM_BACKEND == "openai":
        try:
            from openai import OpenAI
            if not OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY not set; cannot call OpenAI.")
                return None
            client = OpenAI(api_key=OPENAI_API_KEY)

            msgs = _wrap_prompt(query, snippets, lang_code, is_encoder_decoder=False, response_length=response_length)
            logger.debug("[OPENAI PROMPT] %s", msgs)
            print("[OPENAI PROMPT] ", msgs)

            r = client.chat.completions.create(
                model=OPENAI_MODEL, messages=msgs, temperature=0.2, max_tokens=512
            )
            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            answer = r.choices[0].message.content.strip()
            
            # Validate if answer uses context
            if not _validate_context_usage(answer, snippets, query):
                logger.warning("LLM answer appears to use general knowledge instead of context")
                return "I don't have enough information in the provided documents to answer this question.", timing
            
            return answer, timing
        except Exception as e:
            logger.exception("OpenAI generation failed: %s", e)
            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            return None, timing

    # ---------------- OLLAMA ----------------
    if LLM_BACKEND == "ollama":
        try:
            import httpx
            msgs = _wrap_prompt(query, snippets, lang_code, is_encoder_decoder=False, response_length=response_length)
            logger.debug("[OLLAMA PROMPT] %s", msgs)

            payload = {"model": OLLAMA_MODEL, "messages": msgs, "stream": False}
            logger.debug("[OLLAMA PAYLOAD] %s", payload)

            r = httpx.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            answer = (data.get("message") or {}).get("content", "").strip() or None
            
            # Validate if answer uses context
            if answer and not _validate_context_usage(answer, snippets, query):
                logger.warning("LLM answer appears to use general knowledge instead of context")
                return "I don't have enough information in the provided documents to answer this question.", timing
            
            return answer, timing
        except Exception as e:
            logger.exception("Ollama generation failed: %s", e)
            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            return None, timing

    # ---------------- HF TRANSFORMERS ----------------
    if LLM_BACKEND == "hf":
        try:
            from transformers import (
                AutoTokenizer,
                AutoConfig,
                AutoModelForCausalLM,
                AutoModelForSeq2SeqLM,
                pipeline,
            )
            import torch

            config = AutoConfig.from_pretrained(HF_MODEL)
            tok = AutoTokenizer.from_pretrained(HF_MODEL, use_fast=False)

            if config.is_encoder_decoder:
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    HF_MODEL,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else None,
                )
                pipe = pipeline(
                    "text2text-generation",
                    model=model,
                    tokenizer=tok,
                    device=0 if torch.cuda.is_available() else -1,
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    HF_MODEL,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else None,
                )
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tok,
                    device=0 if torch.cuda.is_available() else -1,
                )

            msgs = _wrap_prompt(query, snippets, lang_code, is_encoder_decoder=config.is_encoder_decoder, response_length=response_length)
            prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in msgs])
            logger.debug("[HF PROMPT] %s", prompt)

            if config.is_encoder_decoder:
                out = pipe(prompt, max_new_tokens=HF_MAX_NEW_TOKENS, temperature=HF_TEMPERATURE)
                text = out[0]["generated_text"]
            else:
                out = pipe(
                    prompt,
                    max_new_tokens=HF_MAX_NEW_TOKENS,
                    temperature=HF_TEMPERATURE,
                    do_sample=True,
                )
                raw = out[0]["generated_text"]
                text = raw[len(prompt):].strip() if raw.startswith(prompt) else raw

            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            answer = text.split("Answer:", 1)[-1].strip()
            
            # Validate if answer uses context
            if not _validate_context_usage(answer, snippets, query):
                logger.warning("LLM answer appears to use general knowledge instead of context")
                return "I don't have enough information in the provided documents to answer this question.", timing
            
            return answer, timing

        except Exception as e:
            logger.exception("HF generation failed: %s", e)
            timing = {"llm_generation_ms": round((time.perf_counter() - start_time) * 1000, 4)}
            return None, timing
