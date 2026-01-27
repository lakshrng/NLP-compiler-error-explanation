"""Inference script for T5 model."""
from pathlib import Path
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from src.utils.config import ModelConfig
from src.utils.logger import setup_logger

logger = setup_logger()


class CompilerErrorExplainer:
    """Wrapper class for compiler error explanation inference."""
    
    def __init__(self, model_path: Path = None, config: ModelConfig = None):
        """
        Initialize the explainer.
        
        Args:
            model_path: Path to trained model (uses base model if None)
            config: Model configuration
        """
        if config is None:
            config = ModelConfig()
        
        self.config = config
        
        # Load model and tokenizer
        if model_path and model_path.exists():
            logger.info(f"Loading model from {model_path}")
            self.tokenizer = T5Tokenizer.from_pretrained(str(model_path))
            self.model = T5ForConditionalGeneration.from_pretrained(str(model_path))
        else:
            logger.info(f"Using base model: {config.model_name}")
            self.tokenizer = T5Tokenizer.from_pretrained(config.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(config.model_name)
        
        self.model.eval()
        logger.info("Model loaded and ready for inference")
    
    def explain(self, error_message: str, num_beams: int = 4) -> str:
        """
        Explain a compiler error.
        
        Args:
            error_message: The compiler error message
            num_beams: Number of beams for beam search
            
        Returns:
            Explanation of the error
        """
        # Format input
        input_text = f"explain compiler error: {error_message}"
        
        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.config.max_input_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_encoding['input_ids'],
                attention_mask=input_encoding['attention_mask'],
                max_length=self.config.max_output_length,
                num_beams=num_beams,
                early_stopping=True
            )
        
        # Decode
        explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return explanation

