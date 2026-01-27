"""Evaluation script for T5 model."""
import json
from pathlib import Path
from transformers import T5ForConditionalGeneration, T5Tokenizer
from torch.utils.data import DataLoader
from src.data.dataset import CompilerErrorDataset
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.metrics import compute_metrics

logger = setup_logger()


def evaluate_model(config: Config, model_path: Path = None):
    """
    Evaluate T5 model on test data.
    
    Args:
        config: Configuration object
        model_path: Optional path to trained model (uses base model if None)
    """
    logger.info("Starting model evaluation")
    
    # Load model and tokenizer
    if model_path and model_path.exists():
        logger.info(f"Loading model from {model_path}")
        tokenizer = T5Tokenizer.from_pretrained(str(model_path))
        model = T5ForConditionalGeneration.from_pretrained(str(model_path))
    else:
        logger.info(f"Using base model: {config.model.model_name}")
        tokenizer = T5Tokenizer.from_pretrained(config.model.model_name)
        model = T5ForConditionalGeneration.from_pretrained(config.model.model_name)
    
    model.eval()
    
    # Load test dataset
    test_dataset = CompilerErrorDataset(
        config.data.test_file,
        tokenizer,
        config.model.max_input_length,
        config.model.max_output_length
    )
    
    logger.info(f"Test dataset size: {len(test_dataset)}")
    
    # Load ground truth
    with open(config.data.test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # Generate predictions
    predictions = []
    references = []
    
    logger.info("Generating predictions...")
    for i, sample in enumerate(test_dataset):
        input_ids = sample['input_ids'].unsqueeze(0)
        attention_mask = sample['attention_mask'].unsqueeze(0)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=config.model.max_output_length,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode
        pred_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        ref_text = test_data[i]['target']
        
        predictions.append(pred_text)
        references.append(ref_text)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(test_dataset)} samples")
    
    # Compute metrics
    logger.info("Computing metrics...")
    metrics = compute_metrics(predictions, references)
    
    # Print results
    logger.info("Evaluation Results:")
    for metric, value in metrics.items():
        logger.info(f"  {metric}: {value:.4f}")
    
    # Save results
    results_file = config.training.output_dir / "evaluation_results.json"
    results = {
        'metrics': metrics,
        'predictions': predictions[:10],  # Save first 10 as examples
        'references': references[:10]
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to {results_file}")
    logger.info("Evaluation completed")
    
    return metrics

