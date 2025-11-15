import streamlit as st
import os
import sys
import tempfile
import pandas as pd
import re
import yaml

from env_setup import load_env
from llm_model import init_llm
from run_agent import run_pharma_dbt_agent_from_excel

# Fix for module import if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="DBT Model Generator Agent",
    page_icon="Image/ey_logo.png",
    layout="wide"
)

# ----------------------------
# Hide Streamlit UI elements & top padding
# ----------------------------
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0rem;}
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Logo + Title
# ----------------------------
col1, col2, col3 = st.columns([1, 6, 1])
#with col1:
 #   st.image("Image\DBT_IMAGE.png", width=70)
with col2:
    st.markdown(
        "<h1 style='text-align: center;'>DBT Model Generator Agent</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center;'>Upload your S2T mapping Excel file to generate DBT SQL + YAML + Descriptions</p>",
        unsafe_allow_html=True
    )

# ----------------------------
# Load environment and LLM
# ----------------------------
if not os.path.exists(".env"):
    st.error("❌ .env file not found in project root.")
    st.stop()

try:
    INCUBATOR_KEY, INCUBATOR_ENDPOINT, API_VERSION = load_env()
    llm = init_llm(INCUBATOR_KEY, INCUBATOR_ENDPOINT, API_VERSION)
except Exception as e:
    st.error(f"❌ Failed to load environment or initialize LLM: {e}")
    st.stop()

# ----------------------------
# File uploader
# ----------------------------
uploaded_file = st.file_uploader("📂 Upload your S2T Excel file", type=["xlsx", "xls"])

if uploaded_file:
    st.info("📄 File uploaded successfully. Processing...")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_file.write(uploaded_file.getbuffer())
    temp_file.close()

    log_box = st.empty()
    sql_box = st.empty()
    yaml_box = st.empty()
    desc_box = st.empty()

    try:
        final_result = run_pharma_dbt_agent_from_excel(
            file_path=temp_file.name,
            llm=llm,
            show_logs=True,
            log_callback=lambda msg: log_box.text(msg)
        )

        sql_text = final_result.get("sql", "")
        yaml_text = final_result.get("yaml", "")
        descriptions_text = final_result.get("descriptions", "")

        st.success("✅ DBT model and schema.yml generated!")

        # Display SQL
        if sql_text:
            st.subheader("💾 Generated SQL")
            sql_box.code(sql_text, language="sql")
            st.download_button("⬇ Download SQL", sql_text, file_name="model.sql", mime="text/sql")

        # Display YAML
        if yaml_text:
            st.subheader("🧾 Generated schema.yml")
            yaml_box.code(yaml_text, language="yaml")
            st.download_button("⬇ Download YAML", yaml_text, file_name="schema.yml", mime="text/yaml")

        # Display descriptions
        if descriptions_text:
            st.subheader("📘 Extracted Descriptions")
            desc_box.text_area("Descriptions", descriptions_text, height=300)
            st.download_button("⬇ Download Descriptions", descriptions_text, file_name="descriptions.txt", mime="text/plain")

    except Exception as e:
        st.error(f"❌ Error running DBT Agent: {e}")

# ----------------------------
# Follow-up Q&A section
# ----------------------------
st.markdown("---")
st.subheader("💬 Ask questions about your generated model")

if "llm" not in st.session_state:
    st.session_state.llm = llm
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for role, msg in st.session_state.messages:
    if role == "user":
        st.chat_message("user").markdown(msg)
    else:
        st.chat_message("assistant").markdown(msg)

# Chat input
user_question = st.chat_input("Ask a question about your SQL/YAML, e.g., 'Explain joins', 'Add test cases', etc.")
if user_question:
    st.chat_message("user").markdown(user_question)
    st.session_state.messages.append(("user", user_question))

    if sql_text and yaml_text:
        with st.spinner("Thinking..."):
            try:
                # Inject SQL/YAML/descriptions as context
                context_prompt = f"""
You are a DBT expert. Use the following SQL, YAML, and descriptions to answer the question.

SQL:
{sql_text}

YAML / schema:
{yaml_text}

Descriptions:
{descriptions_text}

Question: {user_question}

Answer based only on the above content.
"""
                response = st.session_state.llm.invoke(context_prompt)
                answer = getattr(response, "content", str(response))
                st.chat_message("assistant").markdown(answer)
                st.session_state.messages.append(("assistant", answer))
            except Exception as e:
                st.error(f"❌ Failed to get response: {e}")
