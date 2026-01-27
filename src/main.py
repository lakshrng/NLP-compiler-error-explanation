"""Main entry point for the compiler error explanation system."""
import argparse
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.data.preprocess import preprocess_data
from src.models.train import train_model
from src.models.evaluate import evaluate_model
from src.models.inference import CompilerErrorExplainer

logger = setup_logger()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Compiler Error Explanation System")
    parser.add_argument(
        '--mode',
        type=str,
        choices=['preprocess', 'train', 'evaluate', 'inference'],
        required=True,
        help='Mode to run: preprocess, train, evaluate, or inference'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='Path to trained model (for evaluate/inference modes)'
    )
    parser.add_argument(
        '--error',
        type=str,
        default=None,
        help='Compiler error message (for inference mode)'
    )
    
    args = parser.parse_args()
    config = Config()
    
    if args.mode == 'preprocess':
        logger.info("Running data preprocessing")
        preprocess_data(config.data)
    
    elif args.mode == 'train':
        logger.info("Running model training")
        train_model(config)
    
    elif args.mode == 'evaluate':
        logger.info("Running model evaluation")
        model_path = Path(args.model_path) if args.model_path else None
        evaluate_model(config, model_path)
    
    elif args.mode == 'inference':
        logger.info("Running inference")
        model_path = Path(args.model_path) if args.model_path else None
        explainer = CompilerErrorExplainer(model_path, config.model)
        
        if args.error:
            explanation = explainer.explain(args.error)
            print(f"\nError: {args.error}")
            print(f"Explanation: {explanation}\n")
        else:
            logger.warning("No error message provided. Use --error flag.")


if __name__ == "__main__":
    main()

