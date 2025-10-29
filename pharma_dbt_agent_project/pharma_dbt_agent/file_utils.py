import os
from datetime import datetime
import re


def save_sql_yaml(final_output: str, output_dir: str = "models", target_entity: str = None):
    """
    Extracts SQL and YAML from the LLM output and saves them as timestamped files inside `models` folder.

    Args:
        final_output (str): The output string from the LLM
        output_dir (str): Directory where files will be saved (default: 'models')
        target_entity (str): Optional target entity name for file naming
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Default name if no target_entity found
    base_name = target_entity if target_entity else "clinical_trial"
    base_name = re.sub(r"[^a-zA-Z0-9_]", "_", base_name)  # sanitize name

    # Extract SQL and YAML blocks
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
