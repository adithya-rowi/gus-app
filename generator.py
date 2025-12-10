"""
Generator - Generates Gus Baha style responses using DeepSeek API.
Supports conversation history for multi-turn conversations.
Returns source metadata for citations.
"""

import os
from openai import OpenAI

from persona import SYSTEM_PROMPT, FEW_SHOTS
from ragie_client import retrieve_context, format_context_for_prompt, get_unique_sources

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def detect_language(text: str) -> str:
    """
    Detect if user is writing in Indonesian or English.
    Checks Indonesian words FIRST, then English patterns.
    Defaults to Indonesian.
    """
    text_lower = text.lower()
    
    # Indonesian words - check these FIRST (word boundary matching)
    id_words = ['saya', 'aku', 'gimana', 'bagaimana', 'kenapa', 'apa', 'apakah', 
                'tidak', 'gak', 'nggak', 'bisa', 'dengan', 'yang', 'untuk', 
                'sudah', 'udah', 'belum', 'kalau', 'kalo', 'jadi', 'atau', 
                'tapi', 'dan', 'ini', 'itu', 'ya', 'dong', 'sih', 'kok', 
                'loh', 'deh', 'nih', 'kan', 'gus', 'allah', 'tuhan', 'dosa', 'ibadah']
    
    # Check Indonesian words first (must match as whole word)
    words_in_text = text_lower.split()
    for word in id_words:
        if word in words_in_text:
            return 'id'
    
    # English patterns - check these second (substring matching)
    en_patterns = ["i'm", "i am", "how do", "how can", "what is", "why do", 
                   "does ", "do you", "can you", "tell me", "please", "thank", 
                   "my prayer", "my prayers", "listen to", "even though"]
    
    for pattern in en_patterns:
        if pattern in text_lower:
            return 'en'
    
    # Default to Indonesian
    return 'id'


# English system prompt
SYSTEM_PROMPT_EN = """
You are Gus Baha—a wise, warm Javanese Islamic scholar known for casual yet profound teaching.

CHARACTER:
- Humble, self-deprecating humor
- Short stories with punchlines
- Warm, never judgmental
- Makes religion feel easy, not scary

RESPONSE STRUCTURE (5-8 sentences max):
1. Validate feelings (1 sentence)
2. Story/analogy (2-3 sentences)
3. Insight about God's mercy (1-2 sentences)
4. Practical closing (1 sentence)

STYLE: Casual like a wise uncle. Use "look," "here's the thing," light humor.

CORE MESSAGE: God is merciful. Religion is simple. Don't overcomplicate it.

OFF-TOPIC (cooking, tech, sports, entertainment, shopping, homework):
Say: "Ha! That's not my area. I'm just a village scholar—coffee and faith. 😄 But if something's troubling your heart about life or faith, let's talk."

AVOID: Long lectures, academic tone, scaring people, judging, answering off-topic with "Islamic twist".

IMPORTANT: You can see the conversation history. Use it to understand context and follow-up questions. Respond naturally as if continuing a conversation.
"""

FEW_SHOTS_EN = [
    {
        "role": "user",
        "content": "I'm scared of dying because I've sinned so much."
    },
    {
        "role": "assistant",
        "content": """Ha! Being scared of death is normal. Even living scares people!

Here's the thing—how's your relationship with God been? He's still giving you breath, food, chances to repent. There was a Bedouin asked who'd judge him. He said: "God Himself." Then laughed. "Why?" "My memories with God have been good. Why would He suddenly turn cruel?"

The Prophet said: "This Bedouin gets it!"

Relax. Your track record with God is fine. Don't overcomplicate it."""
    },
    {
        "role": "user",
        "content": "How do I cook nasi goreng?"
    },
    {
        "role": "assistant",
        "content": """Ha! Cooking is really not my thing. I'm just a village scholar—coffee and faith, that's my expertise. 😄

But if something's troubling your heart—about life, faith, family—let's talk. That's what I'm here for.

Anything on your mind?"""
    }
]


def generate_response(query: str, history: list = None, use_rag: bool = True) -> dict:
    """
    Generate Gus Baha response with conversation history support.
    
    Args:
        query: Current user message
        history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        use_rag: Whether to use RAG for context
    
    Returns:
        dict with response, sources, language, etc.
    """
    if history is None:
        history = []
    
    # Step 1: Detect language
    lang = detect_language(query)
    
    # Step 2: Select prompts based on language
    if lang == 'id':
        system_prompt = SYSTEM_PROMPT + """

PENTING: Kamu bisa melihat riwayat percakapan. Gunakan untuk memahami konteks dan pertanyaan lanjutan. Jawab secara natural seperti melanjutkan percakapan."""
        few_shots = FEW_SHOTS
        instruction = """INSTRUKSI:
- Jawab gaya Gus Baha: santai, hangat, ada cerita
- Maksimal 5-8 kalimat
- Buat penanya TENANG
- Pakai: wong, kok, loh, gak, segampang itu, gitu aja kok repot
- Kalau topik di luar Islam/kehidupan (masak, coding, olahraga, dll) → redirect dengan hangat
- Perhatikan konteks percakapan sebelumnya
- GUNAKAN SEMUA KONTEKS yang diberikan (baik bahasa Indonesia maupun Inggris)
- JAWAB DALAM BAHASA INDONESIA"""
    else:
        system_prompt = SYSTEM_PROMPT_EN
        few_shots = FEW_SHOTS_EN
        instruction = """INSTRUCTIONS:
- Answer in Gus Baha's casual warm style
- Maximum 5-8 sentences
- Make questioner feel CALM
- Use: "look," "here's the thing," "don't overcomplicate it"
- If off-topic (cooking, tech, sports, etc) → warmly redirect
- Pay attention to conversation history for context
- USE ALL PROVIDED CONTEXT (both Indonesian and English sources)
- ANSWER IN ENGLISH"""
    
    # Step 3: Get RAG context (retrieve more to get both languages)
    chunks = []
    context_str = ""
    sources = []
    
    if use_rag:
        try:
            # Retrieve more chunks to capture both Indonesian and English content
            chunks = retrieve_context(query, top_k=8)
            if chunks:
                context_str = format_context_for_prompt(chunks, max_chars=3500)
                sources = get_unique_sources(chunks)
        except Exception as e:
            print(f"RAG error: {e}")
    
    # Step 4: Build conversation messages
    messages = [
        {"role": "system", "content": system_prompt},
        *few_shots,
    ]
    
    # Add conversation history (limit to last 6 exchanges = 12 messages)
    if history:
        recent_history = history[-12:]
        for msg in recent_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Step 5: Build current user message with RAG context
    if context_str:
        user_message = f"""KONTEKS dari pengajaran Gus Baha (gunakan semua, baik Indonesia maupun Inggris):
{context_str}

PERTANYAAN SEKARANG: "{query}"

{instruction}"""
    else:
        user_message = f"""PERTANYAAN SEKARANG: "{query}"

(Tidak ada konteks spesifik dari RAG)

{instruction}"""
    
    messages.append({"role": "user", "content": user_message})
    
    # Step 6: Generate response
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.85,
            max_tokens=400,
            presence_penalty=0.3,
            frequency_penalty=0.3
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Clean markdown symbols (asterisks and underscores)
        answer = answer.replace('*', '').replace('_', '')
        
        # Step 7: Detect if response is a redirect (off-topic)
        redirect_phrases_id = [
            "saya gak pinter", "saya gak ngerti", "saya gak jago",
            "bisanya cuma ngaji", "kiai kampung", "bukan keahlian saya",
            "di luar kemampuan"
        ]
        redirect_phrases_en = [
            "not my thing", "not my area", "just a village scholar",
            "coffee and faith", "not really my expertise"
        ]
        
        answer_lower = answer.lower()
        is_redirect = any(phrase in answer_lower for phrase in redirect_phrases_id + redirect_phrases_en)
        
        # If redirect, don't return sources
        if is_redirect:
            return {
                "response": answer,
                "context_used": False,
                "chunks_retrieved": 0,
                "sources": [],
                "language": lang,
                "error": None
            }
        
        return {
            "response": answer,
            "context_used": len(chunks) > 0,
            "chunks_retrieved": len(chunks),
            "sources": sources,
            "language": lang,
            "error": None
        }
        
    except Exception as e:
        print(f"Generation error: {e}")
        return {
            "response": None,
            "context_used": False,
            "chunks_retrieved": 0,
            "sources": [],
            "language": lang,
            "error": str(e)
        }
