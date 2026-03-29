"""
Complete data preparation:
1. Ensure both train.json and val.json have pairs of (classify_error, explain_error).
2. Refine the explain_error targets algorithmically.
3. Split into task-specific files.
"""
import json
import re
from pathlib import Path

# --- Heuristics (from transform_train_sft.py) ---
def first_compiler_line(compiler_output: str) -> str:
    return compiler_output.split("\n")[0].strip() if compiler_output else ""

def _quoted_identifier(msg: str) -> str:
    m = re.search(r"['\u2018\u2019]([^'\u2018\u2019]+)['\u2018\u2019]", msg)
    return m.group(1).strip() if m else ""

def generate_explanation(code: str, compiler_output: str) -> str:
    msg = compiler_output
    first = msg.split("\n")[0]
    
    # --- Simplified but robust mapping (from refine_explanations.py) ---
    if "cannot convert" in first or "invalid conversion" in first or "conversion from" in first:
        return (
            "A value is being used where a different type is required. "
            "C++ does not allow implicit conversion between incompatible types such as pointers and integers, or between unrelated class types. "
            "Use an explicit cast only when the conversion is well-defined and safe, or change the variable or argument type to match the value you are providing."
        )
    if "narrowing conversion" in first or "narrowing" in first:
        return (
            "A narrowing conversion is attempted in a context that forbids it (e.g. brace initialization). "
            "C++ brace-initialization disallows implicit narrowing from a larger or floating-point type to a smaller or integer type. "
            "Use an explicit cast if the loss of precision is intended, or initialize with a value that fits the target type."
        )
    if "expected" in first and ";" in first:
        if "before" in first and "}" in first:
            return (
                "A statement is missing a semicolon before a closing brace. "
                "In C++, every statement must end with a semicolon. "
                "Add a semicolon after the last statement inside the block."
            )
        return (
            "The parser expected a semicolon at this location. "
            "In C++, statements and declarations end with a semicolon. "
            "Add the missing semicolon where the compiler indicates."
        )
    if "was not declared" in first or "were not declared" in first:
        name = _quoted_identifier(first)
        ident = f" '{name}'" if name else ""
        return (
            f"The name{ident} is used but has not been declared in this scope. "
            "In C++, every identifier must be declared before use. "
            "Declare the variable or function before using it, or fix the spelling."
        )
    
    # Default fallback
    return (
        "The code violates a rule of C++ that the compiler checks. "
        "Fix the construct indicated by the message: correct the syntax, types, or usage so it matches the language rules. "
        "Consult the compiler message for the exact location and adjust the code."
    )

def parse_input(inp: str):
    if "Compiler output:" in inp:
        body = inp.split("classify_error: ", 1)[-1].split("explain_error: ", 1)[-1]
        code_part, out_part = body.split("Compiler output:", 1)
        code = code_part.replace("C++ code:\n", "", 1).strip()
        return code, out_part.strip()
    return "", inp

def process_file(file_path: Path):
    if not file_path.exists():
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure multitask pairs
    multitask_data = []
    for entry in data:
        inp = entry["input"]
        target = entry["target"]
        
        if inp.startswith("classify_error:"):
            # Original classify
            multitask_data.append(entry)
            
            # Create explain pair
            code, compiler_out = parse_input(inp)
            explain_inp = "explain_error: " + inp[len("classify_error: "):]
            explain_target = generate_explanation(code, compiler_out)
            multitask_data.append({"input": explain_inp, "target": explain_target})
        elif inp.startswith("explain_error:"):
            # Already an explanation, keep but maybe refine?
            # For simplicity, we just keep it if it's already there
            multitask_data.append(entry)
            
    # Remove duplicates (some might have been pairs already)
    seen = set()
    final_data = []
    for e in multitask_data:
        k = (e["input"], e["target"])
        if k not in seen:
            final_data.append(e)
            seen.add(k)
            
    # Split into tasks
    classify_data = [e for e in final_data if e["input"].startswith("classify_error:")]
    explain_data = [e for e in final_data if e["input"].startswith("explain_error:")]
    
    # Save files
    stem = file_path.stem
    with open(file_path.parent / f"{stem}_classify.json", 'w', encoding='utf-8') as f:
        json.dump(classify_data, f, indent=2, ensure_ascii=False)
    with open(file_path.parent / f"{stem}_explain.json", 'w', encoding='utf-8') as f:
        json.dump(explain_data, f, indent=2, ensure_ascii=False)
        
    print(f"Processed {file_path.name}: {len(classify_data)} classification, {len(explain_data)} explanation entries.")

def main():
    repo = Path(__file__).resolve().parent.parent
    data_dir = repo / "data" / "processed"
    
    process_file(data_dir / "train.json")
    process_file(data_dir / "val.json")

if __name__ == "__main__":
    main()
