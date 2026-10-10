"""
Streamlit Frontend for the Football Agent
============================================
A simple interface to try different football questions and see:
- which tool (calculator / next match / result / days) the agent used
  for each answer
- a log of questions grouped by tool in the left sidebar
"""

import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Football Agent", page_icon="⚽", layout="wide")

TOOL_ICONS = {
    "calculate_standings": "🧮",
    "days_until_match": "📅",
    "get_next_match": "⏭️",
    "get_match_result": "🏁",
}

TOOL_LABELS = {
    "calculate_standings": "Standings calculator",
    "days_until_match": "Days calculator",
    "get_next_match": "Next match",
    "get_match_result": "Last result",
}

if "history" not in st.session_state:
    st.session_state.history = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Separate log per tool: {"calculate_standings": [question1, question2, ...], ...}
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = {name: [] for name in TOOL_ICONS}


def tools_badge(steps: list) -> str:
    """Returns a short label like '🧮 Standings calculator · 📅 Days calculator'"""
    used = []
    seen = set()
    for step in steps:
        name = step["tool_name"]
        if name not in seen:
            seen.add(name)
            icon = TOOL_ICONS.get(name, "🛠️")
            label = TOOL_LABELS.get(name, name)
            used.append(f"{icon} {label}")
    return " · ".join(used) if used else "No tool (direct answer)"


def render_steps_expander(steps: list, expanded: bool = False):
    if not steps:
        return
    with st.expander(f"🛠️ Details ({len(steps)} tool call(s))", expanded=expanded):
        for step in steps:
            icon = TOOL_ICONS.get(step["tool_name"], "🛠️")
            st.markdown(f"**{icon} {step['tool_name']}** — `{step['args']}`")
            st.text(step["content"][:500])
            st.divider()


# =========================================================
# Sidebar: usage log grouped by tool
# =========================================================
with st.sidebar:
    st.header("📋 Tool usage log")

    for tool_name, icon in TOOL_ICONS.items():
        label = TOOL_LABELS.get(tool_name, tool_name)
        questions = st.session_state.tool_logs[tool_name]
        with st.expander(f"{icon} {label} ({len(questions)})", expanded=False):
            if not questions:
                st.caption("No questions used this tool yet")
            else:
                for q in reversed(questions):  # most recent first
                    st.markdown(f"- {q}")

    st.divider()
    if st.button("🗑️ Clear everything"):
        st.session_state.history = []
        st.session_state.conversation_history = []
        st.session_state.tool_logs = {name: [] for name in TOOL_ICONS}
        st.rerun()


# =========================================================
# Main page: chat
# =========================================================
st.title("⚽ Football Agentic Demo")
st.caption("Groq (Qwen) + TheSportsDB + standings calculator + days calculator — football-only agent")

# --- Render past conversation history ---
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.caption(f"🔧 Used: {tools_badge(entry['steps'])}")
        render_steps_expander(entry["steps"])
        st.write(entry["answer"])

question = st.chat_input("Ask me anything about football...")

if question:
    with st.chat_message("user"):
        st.write(question)

    steps_log = []

    def on_step(step):
        if step["type"] == "tool_call":
            steps_log.append(
                {"tool_name": step["tool_name"], "args": step["args"], "content": ""}
            )
        elif step["type"] == "tool_result":
            for s in reversed(steps_log):
                if s["tool_name"] == step["tool_name"] and s["content"] == "":
                    s["content"] = step["content"]
                    break

    with st.chat_message("assistant"):
        with st.spinner("The agent is thinking..."):
            answer, st.session_state.conversation_history = run_agent(
                question,
                verbose=False,
                on_step=on_step,
                conversation_history=st.session_state.conversation_history,
            )

        st.caption(f"🔧 Used: {tools_badge(steps_log)}")
        render_steps_expander(steps_log, expanded=True)
        st.write(answer)

    # Log this question under every tool it actually used
    used_tools = {s["tool_name"] for s in steps_log}
    for tool_name in used_tools:
        if tool_name in st.session_state.tool_logs:
            st.session_state.tool_logs[tool_name].append(question)

    st.session_state.history.append(
        {"question": question, "steps": steps_log, "answer": answer}
    )