# llm.py (improved with bugfixes + logging)
from typing import List, Optional
from .config import (
    LLM_BACKEND, OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_HOST, OLLAMA_MODEL,
    HF_MODEL, HF_MAX_NEW_TOKENS, HF_TEMPERATURE
)
from .store import store
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

    metaquestion = _is_meta_question(query)

    if metaquestion:
        kb_summary = store.summarize_kb()
        # 🟢 General knowledge mode
        sys = (
            f"You are a document assistant that describes the application's knowledge base and general functions.\n"
            f"Respond in the same language as the user's question ('{lang_code}')."
        )
        user = (
            f"Question: {query}\n\n"
            f"Information about this application's knowledge base:\n{kb_summary}\n\n"
            f"Answer:"
        )
        return [{"role": "system", "content": sys + "\n" + user}]
    
    if is_encoder_decoder:
        # Instruction style (T5/mT5/Marian/mBART)
        sys = (
            f"You are a document assistant that answers questions using the provided context.\n"
            f"RULES:\n"
            f"1. Use ONLY the information from the provided context below to answer the question.\n"
            f"2. If the context does not contain enough information, respond exactly with: "
            f"'I don't have enough information in the provided documents to answer this question.'\n"
            f"3. You may internally translate both the question and the context into any language "
            f"to reason about meaning and semantic equivalence.\n"
            f"4. **All parts of the final answer must be in the same language as the user's question.** This includes translating any text in the context that is not in {lang_code} to {lang_code}.**\n"
            f"4. Treat translated or semantically equivalent terms across languages as identical "
            f"(e.g., 索引 = index, 样本 = sample). This counts as using the context, not inventing facts.\n"
            f"5. If partial but related information exists in the context, summarize it; do not default to 'no information.'\n"
            f"6. If the context contains procedures or step-by-step instructions, list all steps clearly in order.\n"
            f"7. Respond in the same language as the user's question, which is '{lang_code}'.\n"
            f"8. Provide a moderate-length answer with key details.\n"
            f"9. Do NOT include citation markers like [1], [2].\n"
        )

        user = (
            f"The question may be in a different language than the context. "
            f"Please reason about translated equivalents internally before answering.\n\n"
            f"Question: {query}\n\n"
            f"Context from documents:\n{context}\n\n"
            f"Answer (using ONLY the context above, in the same language as the question):"
        )
        return [{"role": "user", "content": sys + "\n" + user}]
    else:
        # Chat style (GPT, LLaMA, etc.)
        sys = (
            f"You are a document assistant that answers questions using the provided context.\n"
            f"RULES:\n"
            f"1. Use ONLY the information from the provided context below to answer the question.\n"
            f"2. If the context does not contain enough information, respond exactly with: "
            f"'I don't have enough information in the provided documents to answer this question.'\n"
            f"3. You may internally translate both the question and the context into any language "
            f"to reason about meaning and semantic equivalence.\n"
            f"4. **All parts of the final answer must be in the same language as the user's question.** This includes translating any text in the context that is not in {lang_code} to {lang_code}.**\n"
            f"4. Treat translated or semantically equivalent terms across languages as identical "
            f"(e.g., 索引 = index, 样本 = sample). This counts as using the context, not inventing facts.\n"
            f"5. If partial but related information exists in the context, summarize it; do not default to 'no information.'\n"
            f"6. If the context contains procedures or step-by-step instructions, list all steps clearly in order.\n"
            f"7. Respond in the same language as the user's question, which is '{lang_code}'.\n"
            f"8. Provide a moderate-length answer with key details.\n"
            f"9. Do NOT include citation markers like [1], [2].\n"
        )

        user = (
            f"The question may be in a different language than the context. "
            f"Please reason about translated equivalents internally before answering.\n\n"
            f"Question: {query}\n\n"
            f"Context from documents:\n{context}\n\n"
            f"Answer (using ONLY the context above, in the same language as the question):"
        )
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
        "what can you help me with", "what topics", "document topics", "files available", "Tell me about the documents in your knowledge base"
    ]
    return any(keyword in query_lower for keyword in meta_keywords)

def _validate_context_usage(answer: str, snippets: List[str], query: str = "") -> bool:
    """
    Validate if the answer appears to use the provided context.
    Returns True if the answer seems to use context, False if it seems like general knowledge.
    """
    print(f"[VALIDATION] Validating answer context usage. Answer length: {len(answer)}, Snippets count: {len(snippets)}")
    if not answer or not snippets:
        print(f"[VALIDATION] No answer or snippets provided, answer : {answer}, snippets: {len(snippets)}")
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
        print(f"[VALIDATION] Answer indicates insufficient context: {answer}")
        return False  # This is a valid "insufficient context" response
    
    return True  # Assume context was used if none of the above conditions matched

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
