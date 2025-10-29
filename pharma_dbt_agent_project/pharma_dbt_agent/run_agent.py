# pharma_dbt_agent/run_agent.py

import pandas as pd
import json
from pharma_dbt_agent.prompt_template import prompt_template
from pharma_dbt_agent.file_utils import save_sql_yaml


def run_pharma_dbt_agent_from_excel(file_path: str, llm, show_logs: bool = True, log_callback=None):
    """
    Reads Excel, converts to JSON, sends to LLM, prints/logs output, saves SQL/YAML.

    Parameters:
        file_path (str): Path to Excel file
        llm: Initialized LLM object
        show_logs (bool): Whether to print logs to console
        log_callback (callable): Optional callback to send log messages (e.g., Streamlit)
    Returns:
        final_output (str): LLM response as string
    """
    try:
        # Load Excel
        df = pd.read_excel(file_path)
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
        )

        # Convert to JSON
        json_data = df.to_dict(orient="records")
        stm_json = json.dumps(json_data, indent=2)

        def log(msg):
            if show_logs:
                print(msg)
            if log_callback:
                log_callback(msg)

        log("\n📄 Excel loaded successfully. Sending JSON to LLM...\n")

        # Prepare input text for LLM
        input_text = f"""{prompt_template}

Here is the S2T Mapping JSON data:
{stm_json}
"""

        # Run LLM
        result = llm.invoke(input_text)
        final_output = result.content if hasattr(result, "content") else str(result)

        log("\n================== 🧠 FINAL OUTPUT ==================\n")
        log(final_output)
        log("\n====================================================\n")

        # --- Extract target entity name (case-insensitive) ---
        target_entity = None
        possible_columns = [c for c in df.columns if "target" in c and "entity" in c]
        if possible_columns:
            col = possible_columns[0]
            target_entity = str(df[col].iloc[0]).strip().lower().replace(" ", "_")

        # Save SQL/YAML using the target_entity name
        save_sql_yaml(final_output, target_entity=target_entity)

        return final_output

    except Exception as e:
        log(f"❌ Error: {e}")
        raise e
