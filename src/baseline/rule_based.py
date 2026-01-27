"""Rule-based baseline for compiler error explanation."""
# This is a placeholder for rule-based baseline implementation

from typing import Dict, List
from pathlib import Path
import json
from src.utils.logger import setup_logger

logger = setup_logger()


class RuleBasedExplainer:
    """Rule-based compiler error explainer."""
    
    def __init__(self, rules_file: Path = None):
        """
        Initialize rule-based explainer.
        
        Args:
            rules_file: Path to JSON file with error patterns and explanations
        """
        self.rules = {}
        if rules_file and rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        logger.info(f"Loaded {len(self.rules)} rules")
    
    def explain(self, error_message: str) -> str:
        """
        Explain error using rule-based matching.
        
        Args:
            error_message: Compiler error message
            
        Returns:
            Explanation if rule matches, otherwise default message
        """
        error_lower = error_message.lower()
        
        # Simple keyword matching
        for pattern, explanation in self.rules.items():
            if pattern.lower() in error_lower:
                return explanation
        
        return "No matching rule found for this error."


if __name__ == "__main__":
    # Example usage
    explainer = RuleBasedExplainer()
    result = explainer.explain("error: 'printf' was not declared in this scope")
    print(result)

