from pathlib import Path
import sys

# Add project root
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.models.inference import CompilerErrorExplainer
from src.utils.config import Config

def test():
    model_path = Path("models/final_t5_model")
    explainer = CompilerErrorExplainer(model_path=model_path)
    
    # EXACT string from train.json (including backticks and exact newlines)
    exact_input = "explain_error: C++ code:\nint x = 10; \ndouble x = 5.5;\nCompiler output:\nerror: conflicting declaration ‘double x’"
    
    print("\n--- TEST: EXACT INPUT ---")
    print(exact_input)
    explanation = explainer.explain(exact_input)
    print("\n--- MODEL OUTPUT ---")
    print(explanation)

if __name__ == "__main__":
    test()
