"""CLI demo for compiler error explanation."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.inference import CompilerErrorExplainer
from src.utils.config import ModelConfig
from src.utils.logger import setup_logger

logger = setup_logger()


def interactive_demo(model_path: Path = None):
    """
    Interactive CLI demo.
    
    Args:
        model_path: Optional path to trained model
    """
    config = ModelConfig()
    explainer = CompilerErrorExplainer(model_path, config)
    
    print("\n" + "="*60)
    print("Compiler Error Explanation System - Interactive Demo")
    print("="*60)
    print("Enter compiler error messages to get explanations.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            error = input("Compiler Error: ").strip()
            
            if error.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not error:
                continue
            
            explanation = explainer.explain(error)
            print(f"\nExplanation: {explanation}\n")
            print("-" * 60 + "\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"An error occurred: {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CLI Demo for Compiler Error Explanation")
    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='Path to trained model'
    )
    
    args = parser.parse_args()
    model_path = Path(args.model_path) if args.model_path else None
    interactive_demo(model_path)

