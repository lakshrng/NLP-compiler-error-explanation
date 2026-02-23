import sys
from pathlib import Path

# Add project root so "src" is importable when running: python demo/cli_rule_based.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.baseline.rule_based import RuleBasedExplainer

explainer = RuleBasedExplainer()

print("Rule-Based Compiler Error Explainer")
print("Type 'exit' to quit\n")

while True:
    user_input = input("Enter compiler error:\n")

    if user_input.lower() == "exit":
        break

    explanation = explainer.explain(user_input)

    print("\n--- Explanation ---\n")
    print(explanation)