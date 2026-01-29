# ai/generate_summary.py
from ai.gemini_client import gemini_call
import pandas as pd

def generate_site_summary(df: pd.DataFrame) -> str:
    """
    Generate a clinical trial site summary using Gemini AI.
    """
    if df.empty:
        return "No data available for the selected filters."

    # Limit rows to avoid huge prompts
    df_prompt = df.head(50)  # adjust as needed

    prompt = f"""
You are a Clinical Trial AI Assistant.

Summarize site performance based on this dataset:

{df_prompt.to_string(index=False)}

Please provide:

1. Overall site performance summary
2. DQI insights
3. Emerging risks
4. CRA action plan (bulleted)
5. Communication message for sponsor
"""

    return gemini_call(prompt)
