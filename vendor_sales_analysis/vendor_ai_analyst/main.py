from groq import Groq
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# ── Setup ─────────────────────────────────────────────────────────────────────
client = Groq(api_key="YOUR_GROQ_KEY_HERE")
MODEL  = "llama-3.3-70b-versatile"
DB_PATH = "D:\\Resume_Projects\\VendorMCP\\data-deepdive-mcp\\inventory.db"

_df           = None
_source_label = ""
_active_table = "sales"
OUTPUT_DIR    = Path("./mcp_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Available tables & their columns ─────────────────────────────────────────
TABLE_SCHEMAS = {}

def load_schemas():
    """Load column names for all tables at startup."""
    global TABLE_SCHEMAS
    engine = create_engine(f"sqlite:///{DB_PATH}")
    tables = ["sales", "purchases", "begin_inventory",
              "end_inventory", "purchase_prices", "vendor_invoice"]
    for t in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {t} LIMIT 1", engine)
            TABLE_SCHEMAS[t] = list(df.columns)
        except Exception:
            pass

# ── Tools ─────────────────────────────────────────────────────────────────────
def load_table(table_name: str):
    global _df, _source_label, _active_table
    engine = create_engine(f"sqlite:///{DB_PATH}")
    _df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 100000", engine)
    _source_label = table_name
    _active_table = table_name
    return f"✅ Loaded {len(_df)} rows from '{table_name}'."

def run_sql_query(query: str) -> str:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        result = pd.read_sql(text(query), conn)
    if len(result) == 0:
        return "Query returned no results."
    return result.to_string(index=False)

def profile_data() -> str:
    if _df is None:
        return "No table loaded."
    return _df.describe().round(2).to_string()

def detect_outliers() -> str:
    if _df is None:
        return "No table loaded."
    import numpy as np
    numeric = _df.select_dtypes(include="number")
    results = []
    for col in numeric.columns:
        Q1, Q3 = numeric[col].quantile(0.25), numeric[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((numeric[col] < Q1 - 1.5*IQR) | (numeric[col] > Q3 + 1.5*IQR)).sum()
        results.append(f"{col}: {outliers} outliers")
    return "\n".join(results)

def list_tables() -> list:
    return list(TABLE_SCHEMAS.keys())

def llm(prompt: str) -> str:
    return client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content.strip()

# ── SQL Generator ─────────────────────────────────────────────────────────────
def generate_sql(question: str) -> str:
    schema_info = "\n".join([
        f"  Table '{t}': columns = {cols}"
        for t, cols in TABLE_SCHEMAS.items()
    ])

    prompt = f"""You are a SQL expert. Generate a single valid SQLite SQL query to answer the question below.

Available tables and their columns:
{schema_info}

Rules:
- Return ONLY the raw SQL query — no explanation, no markdown, no backticks, no comments
- Use exact column names from the schema above
- For cross-table questions use JOIN or subqueries
- Use LIMIT 20 unless the question asks for all results
- Use SUM(), AVG(), COUNT(), GROUP BY where appropriate

Question: {question}

SQL:"""

    sql = llm(prompt)
    # Clean up any accidental markdown
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

# ── Decide which tool to use ──────────────────────────────────────────────────
def route_question(question: str) -> str:
    q = question.lower()

    # Always use SQL for data questions
    data_keywords = [
        "which", "what", "how many", "top", "best", "worst", "highest",
        "lowest", "total", "average", "mean", "sum", "count", "list",
        "show", "find", "compare", "between", "appear", "not in",
        "most", "least", "maximum", "minimum", "revenue", "sales",
        "purchase", "vendor", "product", "inventory", "invoice",
        "profit", "margin", "price", "quantity", "month", "year"
    ]

    profile_keywords = ["profile", "describe", "stats", "overview", "shape", "dtypes"]
    outlier_keywords = ["outlier", "anomaly", "unusual", "extreme", "spike"]

    if any(w in q for w in outlier_keywords):
        return "outliers"
    elif any(w in q for w in profile_keywords):
        return "profile"
    elif any(w in q for w in data_keywords):
        return "sql"
    else:
        return "llm"

# ── Main agent ────────────────────────────────────────────────────────────────
def ask(question: str) -> str:
    route = route_question(question)

    if route == "sql":
        sql = generate_sql(question)
        print(f"\n📊 SQL: {sql}\n")
        try:
            sql_result = run_sql_query(sql)
            # Feed result to LLM for a clean answer
            answer_prompt = f"""You are a data analyst. Answer this question based on the SQL results below.

Question: {question}

SQL Query used: {sql}

Results:
{sql_result}

Give a clear, concise, conversational answer. Use specific numbers from the results."""
            return llm(answer_prompt)

        except Exception as e:
            # If SQL fails, tell LLM what went wrong and ask it to fix
            fix_prompt = f"""The SQL query failed with error: {str(e)}

Original question: {question}
Failed SQL: {sql}

Available tables: {TABLE_SCHEMAS}

Write a corrected SQL query. Return ONLY the SQL, nothing else."""
            fixed_sql = llm(fix_prompt).replace("```sql", "").replace("```", "").strip()
            print(f"\n🔄 Retrying with: {fixed_sql}\n")
            try:
                sql_result = run_sql_query(fixed_sql)
                answer_prompt = f"""Answer this question based on results:
Question: {question}
Results: {sql_result}
Give a clear concise answer with specific numbers."""
                return llm(answer_prompt)
            except Exception as e2:
                return f"Could not execute query. Error: {str(e2)}"

    elif route == "outliers":
        result = detect_outliers()
        return llm(f"Summarize these outlier findings clearly:\n{result}")

    elif route == "profile":
        result = profile_data()
        return llm(f"Summarize this data profile in plain English:\n{result}")

    else:
        # General question — just ask the LLM
        return llm(f"""You are a data analyst assistant working with a beverage industry database.
Tables available: {list_tables()}
Question: {question}
Answer helpfully and concisely.""")


# ── Main loop ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Inventory AI Analyst Ready!\n")
    print("⏳ Loading database schemas...")
    load_schemas()
    print(f"✅ Schemas loaded: {list(TABLE_SCHEMAS.keys())}\n")
    print("💡 Type 'load <table>' to switch tables | 'quit' to exit\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            break
        if question.lower().startswith("load "):
            table = question.split(" ", 1)[1].strip()
            print(load_table(table))
            continue
        if question.lower() == "tables":
            print(f"Available tables: {list_tables()}")
            continue

        print(f"\nAI: {ask(question)}\n")