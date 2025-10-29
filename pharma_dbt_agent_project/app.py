import streamlit as st
import os
import sys
import tempfile
import pandas as pd
from pharma_dbt_agent.env_setup import load_env
from pharma_dbt_agent.llm_model import init_llm
from pharma_dbt_agent.run_agent import run_pharma_dbt_agent_from_excel

# ----------------------------
# Fix for module import if needed
# ----------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ----------------------------
# 1. Page setup
# ----------------------------
st.set_page_config(
    page_title="DBT Model Generator Agent",
    page_icon="Image/ey_logo.png",  # Replace with your favicon/logo path
    layout="wide"
)

# ----------------------------
# Hide Streamlit UI elements & top padding
# ----------------------------
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0rem;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------------------
# Logo + Centered Title
# ----------------------------
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    st.image("Image/ey_logo.png", width=70)  # Replace with your local logo path

with col2:
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 0;'>DBT Model Generator Agent</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center;'>Upload your S2T mapping Excel file and generate DBT-compliant SQL + YAML.</p>",
        unsafe_allow_html=True
    )

# ----------------------------
# 2. Check environment
# ----------------------------
if not os.path.exists(".env"):
    st.error("❌ .env file not found in project root.")
    st.stop()

try:
    INCUBATOR_KEY, INCUBATOR_ENDPOINT, API_VERSION = load_env()
    llm = init_llm(INCUBATOR_KEY, INCUBATOR_ENDPOINT, API_VERSION)
except Exception as e:
    st.error(f"❌ Failed to load environment: {e}")
    st.stop()

# ----------------------------
# 3. File uploader
# ----------------------------
uploaded_file = st.file_uploader(
    "Select your S2T mapping Excel file",
    type=["xlsx", "xls"]
)

if uploaded_file:
    st.info("📄 File uploaded successfully. Running DBT agent...")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_file.write(uploaded_file.getbuffer())
    temp_file.close()

    # ----------------------------
    # Extract target_entity name from Excel
    # ----------------------------
    try:
        df = pd.read_excel(temp_file.name)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
        target_entity = "output"  # default fallback

        possible_cols = [c for c in df.columns if "target" in c and "entity" in c]
        if possible_cols:
            target_entity = str(df[possible_cols[0]].iloc[0]).strip().lower().replace(" ", "_")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
        st.stop()

    # Placeholders for live logs and outputs
    log_box = st.empty()
    sql_box = st.empty()
    yaml_box = st.empty()

    try:
        final_output = run_pharma_dbt_agent_from_excel(
            temp_file.name,
            llm,
            show_logs=True,
            log_callback=lambda msg: log_box.text(msg)
        )

        st.success(f"✅ DBT model and schema.yml generated successfully for '{target_entity}'!")

        import re
        sql_match = re.search(r"```sql(.*?)```", final_output, re.DOTALL)
        yaml_match = re.search(r"```yaml(.*?)```", final_output, re.DOTALL)
        sql_text = sql_match.group(1).strip() if sql_match else None
        yaml_text = yaml_match.group(1).strip() if yaml_match else None

        if sql_text:
            st.subheader("Generated SQL")
            sql_box.code(sql_text, language="sql")
            st.download_button(
                "⬇ Download SQL",
                sql_text,
                file_name=f"{target_entity}.sql",
                mime="text/sql"
            )

        if yaml_text:
            st.subheader("Generated schema.yml")
            yaml_box.code(yaml_text, language="yaml")
            st.download_button(
                "⬇ Download YAML",
                yaml_text,
                file_name=f"{target_entity}.yml",
                mime="text/yaml"
            )

    except Exception as e:
        st.error(f"❌ Error running DBT agent: {e}")
