import json
from pathlib import Path

def split_tasks(input_file: Path, output_dir: Path):
    if not input_file.exists():
        print(f"File {input_file} does not exist.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    classify_data = [e for e in data if e.get("input", "").startswith("classify_error:")]
    explain_data = [e for e in data if e.get("input", "").startswith("explain_error:")]

    classify_file = output_dir / f"{input_file.stem}_classify.json"
    explain_file = output_dir / f"{input_file.stem}_explain.json"

    with open(classify_file, 'w', encoding='utf-8') as f:
        json.dump(classify_data, f, indent=2, ensure_ascii=False)
    
    with open(explain_file, 'w', encoding='utf-8') as f:
        json.dump(explain_data, f, indent=2, ensure_ascii=False)

    print(f"Split {input_file.name} into {classify_file.name} ({len(classify_data)} entries) and {explain_file.name} ({len(explain_data)} entries).")

def main():
    repo = Path(__file__).resolve().parent.parent
    data_dir = repo / "data" / "processed"
    
    split_tasks(data_dir / "train.json", data_dir)
    split_tasks(data_dir / "val.json", data_dir)

if __name__ == "__main__":
    main()
