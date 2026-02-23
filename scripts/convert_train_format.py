"""
Convert train.json to format with both classify_error and explain_error entries.
Each original record becomes two: one classify_error (input -> error type) and one
explain_error (input -> detailed explanation).
"""
import json
import re
from pathlib import Path


def fix_trailing_commas(text: str) -> str:
    """Fix standalone comma lines: turn '}\n,\n\n  {' into '},\n  {'."""
    return re.sub(r"(\})\s*\n\s*,\s*\n\s*(\{)", r"\1,\n  \2", text)


def extract_compiler_output(input_str: str) -> str:
    """Get the part after 'Compiler output:' from a classify_error input."""
    prefix = "classify_error: "
    if not input_str.startswith(prefix):
        return input_str
    body = input_str[len(prefix) :]
    if "Compiler output:" in body:
        _, after = body.split("Compiler output:", 1)
        return after.strip()
    return body.strip()


def make_detailed_explanation(compiler_output: str, classification: str) -> str:
    """Build a short detailed explanation from compiler message and classification."""
    first_line = compiler_output.split("\n")[0].strip()
    return (
        f"The compiler reports: {first_line}. "
        f"This is classified as a {classification}."
    )


def convert_entry(entry: dict) -> list[dict]:
    """Convert one classify_error entry into [classify_entry, explain_entry]."""
    inp = entry["input"]
    target = entry["target"]

    if not inp.startswith("classify_error:"):
        return [entry]

    # Same classify_error entry (keep as-is)
    classify_entry = {"input": inp, "target": target}

    # explain_error: same context, target = detailed explanation
    explain_input = "explain_error: " + inp[len("classify_error: ") :]
    compiler_out = extract_compiler_output(inp)
    detailed = make_detailed_explanation(compiler_out, target)
    explain_entry = {"input": explain_input, "target": detailed}

    return [classify_entry, explain_entry]


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    train_path = data_dir / "train.json"

    raw = train_path.read_text(encoding="utf-8")
    fixed = fix_trailing_commas(raw)
    data = json.loads(fixed)

    out: list[dict] = []
    for item in data:
        out.extend(convert_entry(item))

    train_path.write_text(
        json.dumps(out, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(out)} entries to {train_path} (was {len(data)} classify-only).")


if __name__ == "__main__":
    main()
