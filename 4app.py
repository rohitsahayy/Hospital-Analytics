import streamlit as st
import sqlite3
import pandas as pd
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import PromptTemplate

# -----------------------------
# Streamlit UI Setup
# -----------------------------
st.set_page_config(page_title="Hospital NLQ System", layout="wide")
st.title("Hospital Analytics NLQ Engine")

st.markdown("""
This tool allows you to query the **hospital_warehouse.db** database in plain English.  
For example:
- *Show total treatment cost by department*
- *List top 5 staff by rating*
- *Show average length of stay by patient type*
""")

# -----------------------------
# Step 1: API Key Input
# -----------------------------
api_key = st.text_input("🔑 Enter your Groq API Key:", type="password")

if not api_key:
    st.warning("Please enter your Groq API key to continue.")
    st.stop()

# -----------------------------
# Step 2: Connect to SQLite DB
# -----------------------------
db_path = "hospital_warehouse.db"

try:
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    st.success("✅ Connected to hospital_warehouse.db successfully!")
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# -----------------------------
# Step 3: Initialize LLM (Groq)
# -----------------------------
try:
    llm = ChatGroq(api_key=api_key, model="llama-3.1-8b-instant")
    st.success("✅ Connected to Groq LLM successfully!")
except Exception as e:
    st.error(f"Groq API initialization failed: {e}")
    st.stop()

# -----------------------------
# Step 4: Define Custom Prompt
# -----------------------------
prompt = PromptTemplate(
    input_variables=["input", "table_info"],
    template=(
        "You are an expert data analyst. Given the following hospital database schema, "
        "write a correct SQL query that answers the user’s question. "
        "Return ONLY the SQL query, no explanations.\n\n"
        "Database Schema:\n{table_info}\n\n"
        "User Question:\n{input}\n\n"
        "SQL Query:"
    ),
)

chain = SQLDatabaseChain.from_llm(llm, db, prompt=prompt, verbose=False, return_sql=True)

# -----------------------------
# Step 5: User Query Section
# -----------------------------
st.subheader("Ask your question about the hospital data")
user_query = st.text_area("Enter your question:", placeholder="e.g., Show total treatment cost by department")

if st.button("Run Query"):
    if not user_query.strip():
        st.warning("Please enter a valid question.")
    else:
        with st.spinner("Processing your question..."):
            try:
                # Run the NLQ → SQL → DB execution
                # Run NLQ → SQL → DB execution
                response = chain.run(user_query)  # ✅ simpler + returns text

                # Extract SQL query from response text
                # The chain.run() returns something like "SQL Query: SELECT ...", so we parse it
                if "SELECT" in response.upper():
                    sql_start = response.upper().find("SELECT")
                    sql_query = response[sql_start:].strip().rstrip(";")
                else:
                    sql_query = response.strip()

                st.markdown("Generated SQL Query")
                st.code(sql_query, language="sql")

                # Execute SQL manually to display results
                conn = sqlite3.connect(db_path)
                try:
                    cursor = conn.execute(sql_query)
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    conn.close()

                    # Display data as a table
                    st.markdown("Query Results")
                    if rows:
                        st.dataframe(rows)
                    else:
                        st.info("No results found for this query.")
                except Exception as ex:
                    st.error(f"SQL Execution Error: {ex}")
                    conn.close()


                # Display data as a table
                st.markdown("Query Results")
                if rows:
                    st.dataframe(rows, use_container_width=True)
                else:
                    st.info("No results found for this query.")
            except Exception as e:
                st.error(f"Error while processing query: {e}")





