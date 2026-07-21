# 🧠 AI SQL Query Assistant

Ask questions about a company database in **plain English** — no SQL knowledge required.
This app uses **LangChain** + **Groq** (free, fast LLM inference) to translate natural
language into SQL, execute it against a live SQLite database, and return the answer
alongside the generated query, a results table, and auto-generated charts.

---

## ✨ Features

- 💬 **Natural language → SQL** — ask questions like *"Which employee has the highest salary?"* and get a real answer, not just a query
- 🔍 **Transparent SQL** — every generated query is shown, so you can verify exactly what ran
- 📊 **Auto-visualization** — numeric results are automatically charted
- 📈 **Quick Stats dashboard** — at-a-glance company metrics (headcount, avg. salary, total sales)
- 🗂️ **Schema Explorer** — browse table structure and preview raw data
- 🧠 **Multiple model choices** — switch between Llama 3.3 70B, GPT-OSS 120B/20B, and Llama 3.1 8B (all via Groq)
- 📥 **Exportable chat history** — download your Q&A session as a text transcript

---

## 🏗️ Architecture

```mermaid
flowchart LR
    U["🙋 User<br/>(Streamlit Chat UI)"] -->|"Natural language question"| APP["app.py<br/>Streamlit App"]
    APP -->|"Invoke agent"| AGENT["LangChain SQL Agent<br/>(create_sql_agent)"]
    AGENT -->|"Reason + tool calls"| LLM["Groq LLM<br/>(Llama 3.3 / GPT-OSS)"]
    AGENT -->|"SQL toolkit"| TOOLKIT["SQLDatabaseToolkit"]
    TOOLKIT -->|"Execute query"| DB[("company.db<br/>SQLite")]
    DB -->|"Rows"| TOOLKIT
    TOOLKIT -->|"Observation"| AGENT
    LLM -->|"Final answer"| AGENT
    AGENT -->|"Answer + intermediate steps"| APP
    APP -->|"Answer, SQL, table, chart"| U

    style U fill:#8B5CF6,color:#fff
    style APP fill:#0B0E14,color:#fff,stroke:#8B5CF6
    style AGENT fill:#0B0E14,color:#fff,stroke:#22D3EE
    style LLM fill:#F472B6,color:#0B0E14
    style TOOLKIT fill:#0B0E14,color:#fff,stroke:#F472B6
    style DB fill:#22D3EE,color:#0B0E14
```

**Components:**

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Streamlit | Chat interface, tabs, charts, styling |
| Orchestration | LangChain (`create_sql_agent`) | Decides which SQL tool calls to make, iterates until it has an answer |
| LLM | Groq API (Llama 3.3 70B / GPT-OSS / Llama 3.1 8B) | Converts natural language → SQL reasoning, and SQL results → natural language answer |
| Toolkit | `SQLDatabaseToolkit` | Exposes schema-inspection and query-execution tools to the agent |
| Data | SQLite (`company.db`) | Stores `employees`, `departments`, `sales` tables |

---

## 🔄 Workflow (request lifecycle)

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant Agent as LangChain SQL Agent
    participant Groq as Groq LLM
    participant DB as SQLite (company.db)

    User->>UI: Types question / clicks sample chip
    UI->>UI: Store question as "pending", rerun (prevents duplicate submits)
    UI->>Agent: agent_executor.invoke({"input": question})
    loop Up to max_iterations
        Agent->>Groq: Reasoning step
        Groq-->>Agent: Next action (inspect schema / run SQL / finish)
        Agent->>DB: Execute SQL (if action = query)
        DB-->>Agent: Rows / error
    end
    Agent-->>UI: Final answer + intermediate_steps (incl. SQL used)
    UI->>UI: Extract last SQL query from steps
    UI->>DB: Re-run same SQL directly (for clean DataFrame)
    DB-->>UI: DataFrame
    UI-->>User: Answer + SQL box + results table + bar chart
```

---


## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate the sample database
```bash
python create_db.py
```
This creates `company.db` with sample `employees`, `departments`, and `sales` data.

### 5. Get a free Groq API key
Sign up at [console.groq.com](https://console.groq.com) and generate an API key.

### 6. Run the app
```bash
streamlit run app.py
```
Paste your Groq API key into the sidebar when the app opens in your browser.

---

## 🗄️ Database Schema

| Table | Columns |
|---|---|
| `departments` | `dept_id`, `dept_name` |
| `employees` | `emp_id`, `name`, `dept_id`, `salary`, `hire_date` |
| `sales` | `sale_id`, `emp_id`, `amount`, `sale_date` |

---

## 🧪 Sample Questions to Try

- *Which employee has the highest salary?*
- *List all employees in the Engineering department*
- *What is the total sales amount per employee?*
- *Who joined the company before 2021?*
- *Which department has the most employees?*
- *What is the average salary per department?*

---

## 🖼️ Screenshots

| | | |
|---|---|---|
| ![Screenshot 1](Screenshots/photo1.png) | ![Screenshot 2](Screenshots/photo2.png) | ![Screenshot 3](Screenshots/photo3.png) |
| ![Screenshot 4](Screenshots/photo4.png) | ![Screenshot 5](Screenshots/photo5.png) | ![Screenshot 6](Screenshots/photo6.png) |
| ![Screenshot 7](Screenshots/photo7.png) | ![Screenshot 8](Screenshots/photo8.png) | |

> Screenshots live in the `Screenshots/` folder (capital S) at the project root.
---

## 🎥 Demo

[▶️ Watch the demo](Langchain_demo.mp4)

> The demo video is at the repo root as `Langchain_demo.mp4`, not inside a `demo/` subfolder.

## 🛠️ Tech Stack

- **Frontend/UI:** Streamlit
- **LLM Orchestration:** LangChain (`langchain`, `langchain-community`)
- **LLM Provider:** Groq (`langchain-groq`) — Llama 3.3 70B, GPT-OSS 120B/20B, Llama 3.1 8B
- **Database:** SQLite (via SQLAlchemy)
- **Data handling:** Pandas

---

## ⚠️ Notes & Limitations

- The Groq API key is entered in the UI and used only for that session — it is **never** written to disk or committed to the repo.
- The agent only executes `SELECT`-style queries surfaced through the SQL toolkit; the app additionally re-runs and validates the query as read-only before rendering a DataFrame.
- This is a demo/sample project using a small in-memory-style SQLite database — not intended for production workloads or untrusted multi-user database access.

---

## 📄 License

Add a license of your choice (e.g. MIT) by creating a `LICENSE` file at the project root.

---

## 🙋 Author

AFROSE FATHIMA J
