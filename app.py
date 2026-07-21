"""
AI SQL Query Assistant — Pro
-----------------------------
Ask questions about a company database in plain English.
LangChain converts your question into SQL, runs it, and returns the answer —
plus the generated SQL, a results table, and auto-charts.
Powered by Groq (free, fast inference).
"""

import re
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI SQL Query Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "company.db"

MODEL_OPTIONS = {
    "Llama 3.3 70B Versatile (default, best reasoning)": "llama-3.3-70b-versatile",
    "GPT-OSS 120B (Groq's newer flagship)": "openai/gpt-oss-120b",
    "Llama 3.1 8B Instant (fastest)": "llama-3.1-8b-instant",
    "GPT-OSS 20B (fast + newer)": "openai/gpt-oss-20b",
}

SAMPLE_QUESTIONS = [
    "Which employee has the highest salary?",
    "List all employees in the Engineering department",
    "What is the total sales amount per employee?",
    "Who joined the company before 2021?",
    "Which department has the most employees?",
    "What is the average salary per department?",
]

# ----------------------------------------------------------------------------
# Theme — one consistent dark, professional palette.
# Every text-bearing Streamlit element is targeted explicitly so nothing goes
# invisible, regardless of the viewer's browser/OS light-dark preference.
# ----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
    --bg-0:      #0B0E14;   /* app background base */
    --bg-1:      #10141D;   /* panel background */
    --bg-2:      #161B26;   /* card background */
    --border:    rgba(148, 163, 184, 0.14);
    --border-strong: rgba(148, 163, 184, 0.28);

    --accent-a:  #8B5CF6;   /* violet */
    --accent-b:  #F472B6;   /* pink   */
    --accent-c:  #22D3EE;   /* cyan   */
    --accent-ok: #34D399;   /* green  */

    --text-hi:   #F5F7FA;   /* headings, high-emphasis */
    --text-mid:  #C9D1E0;   /* body text */
    --text-low:  #8A93A6;   /* captions, muted */
    --text-on-accent: #0B0E14;
}

/* ---------- App shell ---------- */
.stApp {
    background:
        radial-gradient(circle at 12% 0%, rgba(139,92,246,0.16), transparent 40%),
        radial-gradient(circle at 88% 8%, rgba(34,211,238,0.14), transparent 42%),
        radial-gradient(circle at 50% 100%, rgba(244,114,182,0.10), transparent 55%),
        var(--bg-0);
    color: var(--text-mid);
}

/* Force every generic text container to a readable color by default */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span,
.stApp div[data-testid="stMarkdownContainer"] {
    color: var(--text-mid);
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: var(--text-hi) !important;
}
.stApp [data-testid="stCaptionContainer"],
.stApp small,
.stApp .stCaption {
    color: var(--text-low) !important;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--bg-1);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * {
    color: var(--text-mid);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--text-hi) !important;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background: var(--bg-2) !important;
    color: var(--text-hi) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: var(--bg-2) !important;
    color: var(--text-hi) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="popover"] * {
    color: var(--text-hi) !important;
}

/* Sample-question chips */
div[data-testid="stSidebar"] .stButton button {
    background: var(--bg-2);
    border: 1px solid var(--border-strong);
    color: var(--text-mid) !important;
    border-radius: 10px;
    padding: 0.5rem 0.9rem;
    font-size: 0.85rem;
    text-align: left;
    width: 100%;
    transition: all 0.15s ease;
}
div[data-testid="stSidebar"] .stButton button:hover {
    background: linear-gradient(120deg, var(--accent-a), var(--accent-b));
    color: var(--text-on-accent) !important;
    border-color: transparent;
    transform: translateY(-1px);
}
div[data-testid="stSidebar"] .stButton button p {
    color: inherit !important;
}

/* ---------- Hero header ---------- */
.hero {
    background: linear-gradient(120deg, var(--accent-a) 0%, var(--accent-b) 55%, var(--accent-c) 100%);
    padding: 2rem 2.2rem;
    border-radius: 18px;
    color: var(--text-on-accent);
    margin-bottom: 1.4rem;
    box-shadow: 0 12px 30px -10px rgba(139, 92, 246, 0.45);
}
.hero h1 {
    font-size: 2.05rem;
    margin: 0 0 0.35rem 0;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-on-accent) !important;
}
.hero p {
    margin: 0;
    color: rgba(11, 14, 20, 0.82) !important;
    font-size: 1.02rem;
}

/* ---------- Stat / metric cards ---------- */
.stat-card {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 6px 18px -12px rgba(0,0,0,0.5);
}
.stat-card .label {
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--accent-c) !important;
    font-weight: 700;
}
.stat-card .value {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--text-hi) !important;
    margin-top: 0.2rem;
}

/* ---------- SQL code block ---------- */
.sql-box {
    border-left: 4px solid var(--accent-c);
    background: #05070C;
    color: #B9F5FF !important;
    padding: 0.85rem 1rem;
    border-radius: 10px;
    font-family: 'Source Code Pro', 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    margin: 0.5rem 0 0.9rem 0;
    overflow-x: auto;
    white-space: pre-wrap;
}

/* ---------- Tabs ---------- */
div[data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--border);
}
button[data-baseweb="tab"] {
    font-weight: 700;
    color: var(--text-low) !important;
    background: transparent;
}
button[data-baseweb="tab"] p {
    color: inherit !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text-hi) !important;
}
div[data-baseweb="tab-highlight"] {
    background: linear-gradient(120deg, var(--accent-a), var(--accent-b)) !important;
    height: 3px;
}

/* ---------- Primary action button ---------- */
.stButton>button[kind="primary"] {
    background: linear-gradient(120deg, var(--accent-a), var(--accent-b));
    color: var(--text-on-accent) !important;
    border: none;
    box-shadow: 0 8px 20px -8px rgba(139, 92, 246, 0.6);
}

/* Generic (main-area) buttons, e.g. download/clear */
.stApp .stButton button,
.stApp .stDownloadButton button {
    background: var(--bg-2);
    color: var(--text-hi) !important;
    border: 1px solid var(--border-strong);
    border-radius: 10px;
}
.stApp .stButton button p,
.stApp .stDownloadButton button p {
    color: inherit !important;
}
.stApp .stButton button:hover,
.stApp .stDownloadButton button:hover {
    border-color: var(--accent-c);
    color: var(--accent-c) !important;
}

/* ---------- Chat bubbles ---------- */
.stChatMessage {
    border-radius: 16px !important;
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
}
.stChatMessage p,
.stChatMessage li,
.stChatMessage span,
.stChatMessage div,
.stChatMessage [data-testid="stMarkdownContainer"] {
    color: var(--text-hi) !important;
}

/* Chat input box */
div[data-testid="stChatInput"] textarea {
    background: var(--bg-2) !important;
    color: var(--text-hi) !important;
    border: 1px solid var(--border-strong) !important;
}
div[data-testid="stChatInput"] {
    background: transparent !important;
}

/* ---------- Dataframes / tables ---------- */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

/* ---------- Alerts (info/error/warning) ---------- */
div[data-testid="stAlert"] {
    background: var(--bg-2) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important;
}
div[data-testid="stAlert"] * {
    color: var(--text-hi) !important;
}

/* ---------- Misc ---------- */
hr { border-color: var(--border) !important; }
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <h1>🧠 AI SQL Query Assistant</h1>
        <p>Ask questions about the company database in plain English —
        LangChain + Groq turn them into SQL, run them, and explain the results.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: role, content, sql, df(records)
if "queued_question" not in st.session_state:
    st.session_state.queued_question = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ----------------------------------------------------------------------------
# Sidebar: setup
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("Groq API Key", type="password", help="Get one free at console.groq.com")
    model_label = st.selectbox("Model", list(MODEL_OPTIONS.keys()), index=0)
    model_name = MODEL_OPTIONS[model_label]

    st.markdown("---")
    st.markdown("**💡 Try a sample question:**")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, key=f"sample_{q}", use_container_width=True):
            st.session_state.queued_question = q

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    with col_b:
        if st.session_state.history:
            transcript = "\n\n".join(
                f"[{turn['role'].upper()}] {turn['content']}"
                + (f"\nSQL: {turn['sql']}" if turn.get("sql") else "")
                for turn in st.session_state.history
            )
            st.download_button(
                "⬇️ Export",
                data=transcript,
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                use_container_width=True,
            )

if not api_key:
    st.info("👈 Enter your Groq API key in the sidebar to get started.")
    st.stop()

# ----------------------------------------------------------------------------
# Data / agent setup (cached)
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_db():
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")


@st.cache_resource(show_spinner=False)
def get_agent(_api_key: str, _model_name: str):
    llm = ChatGroq(model=_model_name, temperature=0, api_key=_api_key)
    toolkit = SQLDatabaseToolkit(db=get_db(), llm=llm)
    # IMPORTANT: use "tool-calling" (generic), not "openai-functions".
    # OPENAI_FUNCTIONS only works with actual OpenAI models — with Llama/Groq
    # it causes the agent to output raw intermediate thoughts instead of a final answer.
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        return_intermediate_steps=True,
    )


db = get_db()
agent_executor = get_agent(api_key, model_name)


def extract_sql_from_steps(intermediate_steps):
    """Pull the last executed SQL query out of the agent's tool-call trace."""
    last_query = None
    for action, _observation in intermediate_steps or []:
        tool_name = getattr(action, "tool", "")
        tool_input = getattr(action, "tool_input", "")
        if "sql_db_query" in tool_name:
            if isinstance(tool_input, dict):
                last_query = tool_input.get("query") or tool_input.get("input")
            else:
                last_query = str(tool_input)
    return last_query


def run_sql_for_dataframe(sql: str):
    """Re-run a SELECT query directly against the sqlite file to get a DataFrame for display/charts."""
    if not sql or not re.match(r"^\s*SELECT", sql, re.IGNORECASE):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Tabs: Chat | Quick Stats | Schema Explorer
# ----------------------------------------------------------------------------
tab_chat, tab_stats, tab_schema = st.tabs(["💬 Chat", "📊 Quick Stats", "🗂️ Schema Explorer"])

# ---- Chat tab ----
with tab_chat:
    for turn in st.session_state.history:
        with st.chat_message(turn["role"], avatar="🙋" if turn["role"] == "user" else "🤖"):
            st.markdown(turn["content"])
            if turn.get("sql"):
                st.markdown(f'<div class="sql-box">{turn["sql"]}</div>', unsafe_allow_html=True)
            if turn.get("df_records"):
                df = pd.DataFrame(turn["df_records"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                numeric_cols = df.select_dtypes(include="number").columns
                if len(df) > 1 and len(numeric_cols) >= 1 and len(df.columns) >= 2:
                    label_col = df.columns[0]
                    value_col = numeric_cols[0]
                    st.bar_chart(df.set_index(label_col)[value_col])

    processing = st.session_state.get("pending_question") is not None

    # Step 1: capture a new question (from a sample chip or the chat box) and
    # immediately store it + rerun, BEFORE calling the (slow) agent. This is what
    # prevents duplicate submissions: once "pending_question" is set, the chat
    # input is disabled below, so a second click/enter can't queue a second one.
    if not processing:
        queued = st.session_state.pop("queued_question", None)
        user_input = st.chat_input("Ask a question about the database…")
        question = queued or user_input
        if question:
            st.session_state.history.append({"role": "user", "content": question})
            st.session_state.pending_question = question
            st.rerun()
    else:
        st.chat_input("Waiting for the previous answer…", disabled=True)

    # Step 2: if there's a pending question, process it now (runs once, right
    # after the rerun above, with the user bubble already shown in history).
    if processing:
        question = st.session_state.pending_question
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking through the schema and writing SQL…"):
                try:
                    result = agent_executor.invoke({"input": question})
                    answer = result["output"]
                    sql = extract_sql_from_steps(result.get("intermediate_steps"))
                    df = run_sql_for_dataframe(sql) if sql else None

                    st.markdown(answer)
                    if sql:
                        st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)
                    df_records = None
                    if df is not None and not df.empty:
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        numeric_cols = df.select_dtypes(include="number").columns
                        if len(df) > 1 and len(numeric_cols) >= 1 and len(df.columns) >= 2:
                            st.bar_chart(df.set_index(df.columns[0])[numeric_cols[0]])
                        df_records = df.to_dict("records")

                    st.session_state.history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sql": sql,
                            "df_records": df_records,
                        }
                    )
                except Exception as e:
                    error_msg = f"Something went wrong: {e}"
                    st.error(error_msg)
                    st.session_state.history.append({"role": "assistant", "content": error_msg})
        st.session_state.pending_question = None
        st.rerun()

# ---- Quick Stats tab ----
with tab_stats:
    st.subheader("Company snapshot")
    conn = sqlite3.connect(DB_PATH)
    try:
        emp_count = pd.read_sql_query("SELECT COUNT(*) AS c FROM employees", conn)["c"][0]
        dept_count = pd.read_sql_query("SELECT COUNT(*) AS c FROM departments", conn)["c"][0]
        avg_salary = pd.read_sql_query("SELECT AVG(salary) AS a FROM employees", conn)["a"][0]
        total_sales = pd.read_sql_query("SELECT COALESCE(SUM(amount), 0) AS s FROM sales", conn)["s"][0]

        c1, c2, c3, c4 = st.columns(4)
        for col, label, value in zip(
            (c1, c2, c3, c4),
            ("Employees", "Departments", "Avg. Salary", "Total Sales"),
            (emp_count, dept_count, f"${avg_salary:,.0f}", f"${total_sales:,.0f}"),
        ):
            col.markdown(
                f'<div class="stat-card"><div class="label">{label}</div>'
                f'<div class="value">{value}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("####")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Employees per department**")
            df_dept = pd.read_sql_query(
                """
                SELECT d.dept_name AS department, COUNT(e.emp_id) AS employees
                FROM departments d
                LEFT JOIN employees e ON e.dept_id = d.dept_id
                GROUP BY d.dept_name
                ORDER BY employees DESC
                """,
                conn,
            )
            st.bar_chart(df_dept.set_index("department")["employees"])
        with colB:
            st.markdown("**Sales total per employee**")
            df_sales = pd.read_sql_query(
                """
                SELECT emp.name AS employee, COALESCE(SUM(s.amount), 0) AS total_sales
                FROM employees emp
                LEFT JOIN sales s ON s.emp_id = emp.emp_id
                GROUP BY emp.name
                HAVING total_sales > 0
                ORDER BY total_sales DESC
                """,
                conn,
            )
            if not df_sales.empty:
                st.bar_chart(df_sales.set_index("employee")["total_sales"])
            else:
                st.caption("No sales records yet.")
    finally:
        conn.close()

# ---- Schema Explorer tab ----
with tab_schema:
    st.subheader("Database schema")
    st.markdown(f'<div class="sql-box">{db.get_table_info()}</div>', unsafe_allow_html=True)

    st.subheader("Table previews")
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'", conn
        )["name"].tolist()
        preview_tabs = st.tabs(tables) if tables else []
        for t, tbl_name in zip(preview_tabs, tables):
            with t:
                st.dataframe(
                    pd.read_sql_query(f"SELECT * FROM {tbl_name} LIMIT 20", conn),
                    use_container_width=True,
                    hide_index=True,
                )
    finally:
        conn.close()