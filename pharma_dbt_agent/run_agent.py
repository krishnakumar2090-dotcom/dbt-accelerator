import pandas as pd
import json
import re
from prompt_template import prompt_template
from file_utils import save_sql_yaml, read_excel_as_json
 
def run_pharma_dbt_agent_from_excel(file_path: str, llm, show_logs: bool = True, log_callback=None):
    """
    Reads Excel, sends to LLM, saves SQL/YAML, extracts descriptions.
    Returns a dict: {"sql": ..., "yaml": ..., "descriptions": ...}
    """
    def log(msg):
        if show_logs:
            print(msg)
        if log_callback:
            log_callback(msg)
 
    try:
        # --- Load Excel ---
        df = pd.read_excel(file_path)
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
        )
        json_data = df.to_dict(orient="records")
        stm_json = json.dumps(json_data, indent=2)
 
        log("📄 Excel loaded successfully. Sending JSON to LLM...")
 
        # --- Prepare LLM input ---
        input_text = f"{prompt_template}\n\nHere is the S2T Mapping JSON data:\n{stm_json}"
 
        # --- Call LLM (string input) ---
        llm_response = llm.invoke(input_text)
        final_output = getattr(llm_response, "content", str(llm_response))
        log("✅ LLM processing complete.\n")
 
        # --- Extract SQL/YAML ---
        sql_match = re.search(r"```sql(.*?)```", final_output, re.DOTALL)
        yaml_match = re.search(r"```yaml(.*?)```", final_output, re.DOTALL)
 
        sql_text = sql_match.group(1).strip() if sql_match else ""
        yaml_text = yaml_match.group(1).strip() if yaml_match else ""
 
        # --- Extract target entity ---
        target_entity = "clinical_trial"
        possible_cols = [c for c in df.columns if "target" in c and "entity" in c]
        if possible_cols:
            target_entity = str(df[possible_cols[0]].iloc[0]).strip().lower().replace(" ", "_")
 
        # --- Save SQL/YAML to disk ---
        save_sql_yaml(final_output, target_entity=target_entity)
 
        # --- Extract descriptions from YAML ---
        descriptions = []
        if yaml_text:
            try:
                import yaml as pyyaml
                yaml_data = pyyaml.safe_load(yaml_text)
                if "models" in yaml_data:
                    for model in yaml_data["models"]:
                        model_name = model.get("name", "")
                        model_desc = model.get("description", "")
                        if model_desc:
                            descriptions.append(f"Model: {model_name}\nDescription: {model_desc}\n")
                        for col in model.get("columns", []):
                            col_name = col.get("name", "")
                            col_desc = col.get("description", "")
                            if col_desc:
                                descriptions.append(f"  Column: {col_name}\n  Description: {col_desc}\n")
            except Exception as e:
                log(f"⚠️ Failed to parse YAML for descriptions: {e}")
 
        return {
            "sql": sql_text,
            "yaml": yaml_text,
            "descriptions": "\n".join(descriptions).strip()
        }
 
    except Exception as e:
        log(f"❌ Error: {e}")
        raise e
 