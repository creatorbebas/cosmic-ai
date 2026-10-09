from core.ai import ask_ai


def analyze_script(
    script,
    language="English"
):
    """
    Menganalisis kualitas script YouTube
    secara menyeluruh.

    Analyzer mengevaluasi:
    - Overall performance
    - Hook strength
    - Retention potential
    - Clarity
    - Story flow
    - Curiosity
    - Setiap section script
    - Strengths
    - Weaknesses
    - Specific improvement recommendations
    """

    if not script or not script.strip():
        return None

    prompt = f"""
You are a senior YouTube script strategist and
audience-retention analyst.

Analyze the following YouTube script as if you were
reviewing it for a professional YouTube channel.

SCRIPT:
{script}

LANGUAGE:
{language}

Your analysis must focus on:

1. HOOK STRENGTH
How effectively the opening creates immediate
attention and curiosity.

2. RETENTION POTENTIAL
How likely the script is to keep viewers watching.

3. CLARITY
How clearly the ideas, information, and narrative
are communicated.

4. STORY FLOW
How naturally the script progresses from one idea
to the next.

5. CURIOSITY
How effectively the script creates unanswered
questions and curiosity gaps.

Also analyze these sections individually when they
exist:

- HOOK
- INTRO
- SEGMENT 1
- SEGMENT 2
- SEGMENT 3
- TWIST
- CLOSING

For every section that exists, provide:

- score from 0 to 100
- status
- specific diagnosis
- specific improvement

Use these status values only:

"excellent"
"strong"
"good"
"needs_work"
"weak"

Do not give generic advice.

Every weakness and recommendation must explain
what is wrong and what should specifically change.

Also provide:

- 3 strengths
- 3 weaknesses
- 3 specific recommendations

Calculate the overall score from the five main
performance scores.

Use this exact JSON structure:

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
      "diagnosis": "Specific explanation of the problem.",
      "improvement": "Specific explanation of how to improve it."
    }}
  ],

  "strengths": [
    "Specific strength 1.",
    "Specific strength 2.",
    "Specific strength 3."
  ],

  "weaknesses": [
    "Specific weakness 1.",
    "Specific weakness 2.",
    "Specific weakness 3."
  ],

  "recommendations": [
    "Specific recommendation 1.",
    "Specific recommendation 2.",
    "Specific recommendation 3."
  ]
}}

IMPORTANT RULES:

- Return ONLY valid JSON.
- Do not use Markdown.
- Do not use code fences.
- Do not add explanations outside the JSON.
- Scores must be integers from 0 to 100.
- Overall must be an integer from 0 to 100.
- Do not invent sections that do not exist.
- Keep the analysis specific to the actual script.
- Do not rewrite the script.
- Do not change the meaning of the script.
"""

    try:

        result = ask_ai(prompt)

        if not result:
            return None

        return result.strip()

    except Exception as error:

        print(
            f"Script analyzer error: {error}"
        )

        return None