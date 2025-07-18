
import random
import requests
import os
import logging
from .content_retrieval import retrieve_relevant_facts

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# API keys and URLs from environment variables for security
CHUTES_API_KEY = os.environ.get("CHUTES_API_KEY", "")
CHUTES_API_URL = os.environ.get("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

def generate_trivia_from_fact(fact):
    """
    Given a fact (WikiArticle or WikiGlossary instance), generate a trivia question.
    Replace the logic below with an LLM call for more advanced generation.
    """
    # Example: simple question from fact
    if hasattr(fact, 'summary'):
        context = fact.summary
    elif hasattr(fact, 'definition'):
        context = fact.definition
    else:
        context = str(fact)

    # Placeholder: generate a simple question and options
    question = f"What is the following about?\n\n{context}"
    options = [
        getattr(fact, 'title', None) or getattr(fact, 'term', None) or "Baybayin",
        "Tagalog",
        "Spanish",
        "English"
    ]
    random.shuffle(options)
    answer = getattr(fact, 'title', None) or getattr(fact, 'term', None) or "Baybayin"

    return {
        "question": question,
        "options": options
    }

# LLM integration using Deepseek (Chutes)
def generate_trivia_with_deepseek(fact):
    """
    Use Deepseek (Chutes) API to generate a trivia question from a fact.
    Returns a dict with question, options, and answer.
    """
    context = getattr(fact, 'summary', None) or getattr(fact, 'definition', None) or str(fact)
    prompt = f"""
Context:
{context}

Task:
Generate a multiple-choice trivia question about Baybayin based on the context above.
Provide 4 options and indicate the correct answer in JSON format:
{{
  "question": "...",
  "options": ["...", "...", "...", "..."],
  "answer": "..."
}}
"""

    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.7
    }
    try:
        response = requests.post(CHUTES_API_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Deepseek API error: {e}")
        return {"question": "[LLM API error]", "options": [], "answer": ""}

    # Try to extract the JSON from the LLM's response
    import json, re
    try:
        # Extract JSON block from the response
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            trivia = json.loads(match.group())
            return trivia
        else:
            logger.warning("Deepseek response did not contain JSON block.")
            return {"question": content, "options": [], "answer": ""}
    except Exception as e:
        logger.error(f"Deepseek JSON parse error: {e}")
        return {"question": content, "options": [], "answer": ""}
# If you want to integrate with an LLM, you can add a function like:
def generate_trivia_with_llm(fact, provider="deepseek", llm_client=None):
    """
    Use an LLM to generate a trivia question from a fact.
    provider: 'deepseek' or 'openai'.
    llm_client: optional, for custom LLM clients (e.g., OpenAI SDK).
    """
    prompt = f"""
Context:
{fact.summary if hasattr(fact, 'summary') else fact.definition}

Task:
Generate a multiple-choice trivia question about Baybayin based on the context above.
Provide 4 options and indicate the correct answer in JSON format:
{{
  "question": "...",
  "options": ["...", "...", "...", "..."],
  "answer": "..."
}}
"""
    if provider == "deepseek":
        return generate_trivia_with_deepseek(fact)
    elif provider == "openai":
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not set.")
            return {"question": "[OpenAI API key not set]", "options": [], "answer": ""}
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.7
        }
        try:
            response = requests.post(OPENAI_API_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"question": "[LLM API error]", "options": [], "answer": ""}
        import json, re
        try:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                trivia = json.loads(match.group())
                return trivia
            else:
                logger.warning("OpenAI response did not contain JSON block.")
                return {"question": content, "options": [], "answer": ""}
        except Exception as e:
            logger.error(f"OpenAI JSON parse error: {e}")
            return {"question": content, "options": [], "answer": ""}
    elif llm_client:
        response = llm_client.generate(prompt)
        return response  # Should return a dict with question, options, answer
    else:
        logger.error("No valid LLM provider specified.")
        return {"question": "[No LLM provider]", "options": [], "answer": ""}

def build_rag_prompt(facts):
    """
    Combine multiple facts into a single context string for the LLM.
    """
    context = "\n\n".join(
        getattr(f, 'summary', None) or getattr(f, 'definition', None) or str(f)
        for f in facts
    )
    prompt = f"""
Context:
{context}

Task:
Generate a multiple-choice trivia question about Baybayin based on the context above.
Provide 4 options and indicate the correct answer in JSON format:
{{
  "question": "...",
  "options": ["...", "...", "...", "..."],
  "answer": "..."
}}
"""
    return prompt

def generate_trivia_with_rag(query, provider="deepseek"):
    """
    Retrieve relevant facts, build a RAG prompt, and send to the LLM.
    provider: 'deepseek' or 'openai'.
    """
    facts = retrieve_relevant_facts(query, top_k=3)
    prompt = build_rag_prompt(facts)
    if provider == "deepseek":
        headers = {
            "Authorization": f"Bearer {CHUTES_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.7
        }
        try:
            response = requests.post(CHUTES_API_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Deepseek API error: {e}")
            return {"question": "[LLM API error]", "options": [], "answer": ""}
    elif provider == "openai":
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not set.")
            return {"question": "[OpenAI API key not set]", "options": [], "answer": ""}
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.7
        }
        try:
            response = requests.post(OPENAI_API_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"question": "[LLM API error]", "options": [], "answer": ""}
    else:
        logger.error("No valid LLM provider specified for RAG.")
        return {"question": "[No LLM provider]", "options": [], "answer": ""}

    import json, re
    try:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            trivia = json.loads(match.group())
            return trivia
        else:
            logger.warning("RAG LLM response did not contain JSON block.")
            return {"question": content, "options": [], "answer": ""}
    except Exception as e:
        logger.error(f"RAG LLM JSON parse error: {e}")
        return {"question": content, "options": [], "answer": ""}

if __name__ == "__main__":
    # Mock a fact (replace with DB fetch if desired)
    class Fact:
        summary = "Baybayin is an ancient script used in the Philippines before Spanish colonization."
        title = "Baybayin"

    fact = Fact()

    # Test prompt building
    facts = [fact, Fact()]
    prompt = build_rag_prompt(facts)
    print("\n[Prompt for RAG]:\n", prompt)

    # Choose which generator to use
    # trivia = generate_trivia_from_fact(fact)
    # trivia = generate_trivia_with_deepseek(fact)
    # trivia = generate_trivia_with_llm(fact, provider="openai")
    # RAG with Deepseek
    # trivia = generate_trivia_with_rag("Baybayin", provider="deepseek")
    # RAG with OpenAI
    # trivia = generate_trivia_with_rag("Baybayin", provider="openai")

    # For demonstration, use the classic generator
    trivia = generate_trivia_from_fact(fact)

    print("\nTrivia Question:")
    print(trivia["question"])
    print("Options:")
    for idx, opt in enumerate(trivia["options"], 1):
        print(f"{idx}. {opt}")

    # Simple test for parsing
    if "answer" in trivia:
        user_choice = input("Your answer (type the option text): ").strip()
        if user_choice.lower() == trivia["answer"].lower():
            print("Correct!")
        else:
            print(f"Incorrect. The correct answer is: {trivia.get('answer', '[unknown]')}")

