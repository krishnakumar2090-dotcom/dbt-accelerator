import os
import json
import re
import pandas as pd
from datetime import datetime


def read_excel_as_json(file_path: str) -> str:
    """Reads Excel and returns JSON string."""
    df = pd.read_excel(file_path)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return json.dumps(df.to_dict(orient="records"), indent=2)


def detect_target_entity(file_path: str) -> str:
    """Detects 'target_entity' column in Excel if present."""
    df = pd.read_excel(file_path)
    target_col = [c for c in df.columns if "target" in c.lower() and "entity" in c.lower()]
    
    if target_col:
        col = target_col[0]
        entity = str(df[col].iloc[0]).strip().lower().replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_]", "_", entity)

    return "clinical_trial"   # fallback


def save_sql_yaml(final_output: str, output_dir: str = "models", target_entity: str = None):
    """Extracts and saves SQL and YAML parts from LLM output."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_name = re.sub(r"[^a-zA-Z0-9_]", "_", target_entity or "clinical_trial")

    sql_match = re.search(r"```sql(.*?)```", final_output, re.DOTALL)
    yaml_match = re.search(r"```yaml(.*?)```", final_output, re.DOTALL)

    sql_text = sql_match.group(1).strip() if sql_match else None
    yaml_text = yaml_match.group(1).strip() if yaml_match else None

    if sql_text:
        sql_file = os.path.join(output_dir, f"{base_name}_{timestamp}.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write(sql_text)
        print(f"✅ SQL saved: {sql_file}")

    if yaml_text:
        yaml_file = os.path.join(output_dir, f"{base_name}_{timestamp}.yml")
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write(yaml_text)
        print(f"✅ YAML saved: {yaml_file}")


def save_sql_yaml_tool(output: str, excel_path: str) -> str:
    """Wrapper tool that dynamically detects target_entity from Excel."""
    entity = detect_target_entity(excel_path)
    save_sql_yaml(output, target_entity=entity)
    return f"✅ SQL/YAML saved for entity: {entity}"
