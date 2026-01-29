from ai.gemini_client import gemini_call

def generate_agent_recommendations(df):
    if df.empty:
        return "No data to evaluate agentic recommendations."

    # Simple rule baseline
    avg = df.dqi.mean()
    alerts = df.alert_flag.sum()

    rules = []
    if avg < 60: rules.append("DQI is critically low — immediate site intervention recommended.")
    if alerts > 5: rules.append("High alert frequency — escalate to regional manager.")
    if df.metric1.mean() > 80: rules.append("Metric1 unusually high — potential protocol deviation.")
    if df.metric2.mean() < 20: rules.append("Metric2 too low — data completeness issue.")

    rule_summary = "\n".join([f"- {r}" for r in rules]) or "No major risks detected."

    llm_prompt = f"""
    Improve and expand these rule-based risk signals:

    {rule_summary}

    Output a prioritized action plan written by a senior clinical operations expert.
    """

    return gemini_call(llm_prompt)
