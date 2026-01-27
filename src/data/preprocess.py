"""Data preprocessing for compiler error explanation."""
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
from src.utils.config import DataConfig
from src.utils.logger import setup_logger

logger = setup_logger()


def load_raw_data(raw_data_dir: Path) -> List[Dict[str, str]]:
    """
    Load raw error data from text files.
    
    Args:
        raw_data_dir: Directory containing raw data files
        
    Returns:
        List of dictionaries with 'error' and 'explanation' keys
    """
    data = []
    
    # Load GCC errors
    gcc_file = raw_data_dir / "gcc_errors.txt"
    if gcc_file.exists():
        logger.info(f"Loading GCC errors from {gcc_file}")
        with open(gcc_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    data.append({
                        'error': lines[i].strip(),
                        'explanation': lines[i + 1].strip(),
                        'compiler': 'gcc'
                    })
    
    # Load Clang errors
    clang_file = raw_data_dir / "clang_errors.txt"
    if clang_file.exists():
        logger.info(f"Loading Clang errors from {clang_file}")
        with open(clang_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    data.append({
                        'error': lines[i].strip(),
                        'explanation': lines[i + 1].strip(),
                        'compiler': 'clang'
                    })
    
    # Load general explanations
    explanations_file = raw_data_dir / "explanations.txt"
    if explanations_file.exists():
        logger.info(f"Loading explanations from {explanations_file}")
        with open(explanations_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    data.append({
                        'error': lines[i].strip(),
                        'explanation': lines[i + 1].strip(),
                        'compiler': 'generic'
                    })
    
    logger.info(f"Loaded {len(data)} error-explanation pairs")
    return data


def format_for_t5(error: str, explanation: str = None) -> Dict[str, str]:
    """
    Format data for T5 model (text-to-text format).
    
    Args:
        error: Compiler error message
        explanation: Optional explanation (for training)
        
    Returns:
        Dictionary with 'input' and optionally 'target'
    """
    input_text = f"explain compiler error: {error}"
    
    if explanation:
        return {
            'input': input_text,
            'target': explanation
        }
    return {'input': input_text}


def split_data(
    data: List[Dict[str, str]],
    train_split: float = 0.8,
    val_split: float = 0.1,
    test_split: float = 0.1,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split data into train, validation, and test sets.
    
    Args:
        data: List of data samples
        train_split: Proportion for training
        val_split: Proportion for validation
        test_split: Proportion for testing
        seed: Random seed
        
    Returns:
        Tuple of (train, val, test) datasets
    """
    random.seed(seed)
    random.shuffle(data)
    
    n = len(data)
    train_end = int(n * train_split)
    val_end = train_end + int(n * val_split)
    
    train_data = data[:train_end]
    val_data = data[train_end:val_end]
    test_data = data[val_end:]
    
    logger.info(f"Split data: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test")
    return train_data, val_data, test_data


def preprocess_data(config: DataConfig) -> None:
    """
    Main preprocessing function.
    
    Args:
        config: Data configuration
    """
    logger.info("Starting data preprocessing")
    
    # Load raw data
    raw_data = load_raw_data(config.raw_data_dir)
    
    if not raw_data:
        logger.warning("No raw data found. Please add data files to data/raw/")
        return
    
    # Limit samples if specified
    if config.max_samples and len(raw_data) > config.max_samples:
        raw_data = raw_data[:config.max_samples]
        logger.info(f"Limited to {config.max_samples} samples")
    
    # Format for T5
    formatted_data = []
    for item in raw_data:
        formatted = format_for_t5(item['error'], item['explanation'])
        formatted['compiler'] = item.get('compiler', 'generic')
        formatted_data.append(formatted)
    
    # Split data
    train_data, val_data, test_data = split_data(
        formatted_data,
        config.train_split,
        config.val_split,
        config.test_split
    )
    
    # Save processed data
    config.processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config.train_file, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved training data to {config.train_file}")
    
    with open(config.val_file, 'w', encoding='utf-8') as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved validation data to {config.val_file}")
    
    with open(config.test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved test data to {config.test_file}")
    
    logger.info("Data preprocessing completed")

