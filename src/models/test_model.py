from transformers import T5Tokenizer, T5ForConditionalGeneration
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "final_t5_model"
# Load model + tokenizer
tokenizer = T5Tokenizer.from_pretrained(str(MODEL_PATH))
model = T5ForConditionalGeneration.from_pretrained(str(MODEL_PATH))


def get_model_output(error_text, task_prefix="classify_error: "):
    input_text = task_prefix + error_text

    inputs = tokenizer(input_text, return_tensors="pt")

    outputs = model.generate(
        **inputs,
        max_length=256
    )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return result


# ---- TEST CASES ----
if __name__ == "__main__":

    test_errors = [
        "error: cannot convert ‘int*’ to ‘double*’",
        "error: no matching function for call to f(int, double)",
        "error: ‘x’ was not declared in this scope",
        "error: lvalue required as left operand of assignment"
    ]

    for err in test_errors:
        print("\n" + "="*50)
        print("INPUT ERROR:", err)
        print("-" * 20)
        print("CLASSIFICATION:", get_model_output(err, "classify_error: "))
        print("EXPLANATION:", get_model_output(err, "explain_error: "))