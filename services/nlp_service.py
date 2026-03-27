import os
import json
import asyncio
import re
from groq import AsyncGroq

# Initialize Async Groq Client from environment
# NOTE: The system initializes this by calling load_dotenv() at project root
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

async def analyze_comment_topics(comments_list: list) -> list:
    """
    Completely rewritten NLP analyze function using Groq's high-performance LLM.
    Identifies semantic topic categories from English, Bengali, and Banglish text.
    Returns: list of dicts [{"topic": str, "percentage": float}]
    """
    if not comments_list:
        return []

    # 1. Extract only the text data for analysis
    texts = [c.get("text", "") for c in comments_list if c.get("text")]
    if not texts:
        return []

    # Pre-clean texts: remove newlines/tabs to keep the prompt clean
    clean_texts = [re.sub(r'\s+', ' ', t).strip() for t in texts]
    
    # Format comments for the prompt
    comments_str = "\n".join([f"- {txt}" for txt in clean_texts])

    prompt = f"""
    Act as an expert data analyst and linguist specializing in multilingual sentiment and topic analysis.
    
    TASK:
    Analyze the following list of social media comments. These comments are written in English, Bengali, and Banglish (Bengali phonetically written in Latin script).
    
    REQUIREMENTS:
    1. READ and CLUSTER the comments based on their TRUE SEMANTIC MEANING and CONTEXT.
    2. Group similar sentiments and themes into distinct, dynamically named TOPICS. 
       - Examples: "PUBG best" and "Love this game" might fall under "Game Appreciation".
       - Categorize based on intent, even across different languages.
    3. CATEGORY NAMES: Must be descriptive, professional, and clearly summarized.
    4. NO OTHERS: Do NOT use "Others", "Miscellaneous", or "General" categories. Every single comment MUST be forced into a logical specific category.
    5. CALCULATE exact percentages for each category (Sum must be exactly 100%).
    
    COMMENTS:
    {comments_str}
    
    OUTPUT FORMAT:
    Return ONLY a valid JSON array of objects.
    NO conversational text, NO markdown code blocks, NO preamble.
    Example Format: 
    [
      {{"topic": "Product Praise", "percentage": 40.0}},
      {{"topic": "Bug Reports", "percentage": 60.0}}
    ]
    """

    try:
        # Calling Groq API (using llama-3.3-70b-versatile as llama3-70b-8192 is decommissioned)
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized multilingual topic analysis engine that outputs ONLY RAW JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0, # Deterministic output
            max_tokens=2048
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Handle potential LLM backticks or extra text in response
        if "```" in response_text:
            # Extract JSON from within markdown blocks
            json_match = re.search(r'\[\s*{.*}\s*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            else:
                response_text = re.sub(r'^```(?:json)?\n?|\n?```$', '', response_text).strip()

        # Parse JSON output
        results = json.loads(response_text)


        # Validate structure is a list
        if not isinstance(results, list):
            raise ValueError("LLM response is not a JSON list")

        # Sort results by percentage (descending)
        results.sort(key=lambda x: x.get("percentage", 0), reverse=True)

        return results

    except Exception as e:
        print(f"ERROR in NLP (Groq): {e}")
        # Fallback in case of API failure or JSON parsing errors
        return [
            {"topic": "Semantic Analysis Unavailable", "percentage": 100.0}
        ]
