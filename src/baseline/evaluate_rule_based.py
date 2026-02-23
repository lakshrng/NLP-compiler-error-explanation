import json
from pathlib import Path

from rule_based import RuleBasedExplainer


def evaluate(dataset_path):
    explainer = RuleBasedExplainer()

    path = Path(dataset_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    correct = 0
    total = 0

    for item in data:
        if item["input"].startswith("classify_error"):
            predicted = explainer.classify(item["input"])
            if predicted == item["target"]:
                correct += 1
            total += 1

    accuracy = correct / total if total > 0 else 0

    print(f"Classification Accuracy: {accuracy:.2f}")
    print(f"Rule Coverage: {explainer.coverage():.2f}")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    dataset_path = repo_root / "data" / "processed" / "train.json"
    evaluate(str(dataset_path))