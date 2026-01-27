"""T5 model setup and configuration."""
from transformers import T5ForConditionalGeneration, T5Tokenizer
from src.utils.config import ModelConfig
from src.utils.logger import setup_logger

logger = setup_logger()


def load_model_and_tokenizer(config: ModelConfig):
    """
    Load T5 model and tokenizer.
    
    Args:
        config: Model configuration
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {config.model_name}")
    
    tokenizer = T5Tokenizer.from_pretrained(config.model_name)
    model = T5ForConditionalGeneration.from_pretrained(config.model_name)
    
    logger.info("Model and tokenizer loaded successfully")
    return model, tokenizer

