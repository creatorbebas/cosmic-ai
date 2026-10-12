from core.ai import ask_ai, parse_json_response

def analyze_script(script, language="English"):
    if not script or not script.strip():
        return None

    prompt = f"""
You are a senior YouTube script strategist and audience-retention analyst.
Analyze the following YouTube script as if you were reviewing it for a professional YouTube channel.

SCRIPT:
{script}

LANGUAGE:
{language}

Your analysis must focus on:
1. HOOK STRENGTH
2. RETENTION POTENTIAL
3. CLARITY
4. STORY FLOW
5. CURIOSITY

Also analyze sections if they exist (HOOK, INTRO, SEGMENT 1, 2, 3, TWIST, CLOSING), providing score (0-100), status, diagnosis, and improvement.
Provide 3 strengths, 3 weaknesses, and 3 specific recommendations. Calculate overall score.

Return ONLY valid JSON matching this exact structure:
{{
  "scores": {{
    "hook_strength": 0,
    "retention_potential": 0,
    "clarity": 0,
    "story_flow": 0,
    "curiosity": 0,
    "overall": 0
  }},
  "status": "good",
  "section_analysis": [
    {{
      "section": "HOOK",
      "score": 0,
      "status": "needs_work",
      "diagnosis": "...",
      "improvement": "..."
    }}
  ],
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "recommendations": ["...", "...", "..."]
}}
"""
    try:
        result = ask_ai(prompt)
        if not result:
            return None
        parsed = parse_json_response(result)
        return parsed if parsed else None
    except Exception as error:
        print(f"Script analyzer error: {error}")
        return None