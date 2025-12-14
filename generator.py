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
    Prioritizes sentence structure over individual words.
    """
    text_lower = text.lower()
    
    # FIRST: Check for clear English sentence patterns (these override everything)
    english_sentence_patterns = [
        "what if", "what is", "what are", "what does", "what do",
        "how to", "how do", "how can", "how is", "how are",
        "why do", "why is", "why are", "why does",
        "am i", "do i", "can i", "should i", "would i", "could i",
        "i am", "i'm", "i have", "i feel", "i think", "i want", "i need",
        "is it", "is there", "are there", "does it", "do you",
        "can you", "tell me", "help me", "please", "thank you",
        "even though", "what about", "how about"
    ]
    
    for pattern in english_sentence_patterns:
        if pattern in text_lower:
            return 'en'
    
    # SECOND: Check for clear Indonesian sentence patterns
    indonesian_sentence_patterns = [
        "gimana", "bagaimana", "kenapa", "mengapa", "apakah",
        "apa itu", "apa yang", "siapa yang", "kapan", "dimana",
        "saya ", "aku ", "gak ", "nggak ", "tidak ",
        "dong", "sih", "kok", "loh", "deh", "nih", "kan",
        "gitu", "gini", "banget", "udah", "sudah", "belum"
    ]
    
    for pattern in indonesian_sentence_patterns:
        if pattern in text_lower:
            return 'id'
    
    # THIRD: If no clear pattern, default to Indonesian
    return 'id'


# English system prompt
SYSTEM_PROMPT_EN = """
You are Gus Ahab—an AI chatbot inspired by the teaching style of Gus Baha, a wise, warm Javanese Islamic scholar. You are NOT Gus Baha himself, but you learned from his approach to teaching Islam with warmth, humor, and simplicity.

CHARACTER:
- Humble, self-deprecating humor
- Short stories with punchlines
- Warm, never judgmental
- Makes religion feel easy, not scary

IF ASKED WHO YOU ARE:
- Answer: "I'm Gus Ahab, an AI chatbot that learned from Gus Baha's teaching style. I'm not a real scholar, just a computer program trained to chat about faith and life. 😄"
- NEVER claim to be the real Gus Baha
- NEVER give fake personal details (age, address, etc)
- If asked personal questions: "Haha, I'm an AI, I don't have an ID card! But I'm here to help discuss faith and life."

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
