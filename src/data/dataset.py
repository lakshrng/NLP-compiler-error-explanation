"""Dataset class for T5 model training."""
import json
from pathlib import Path
from typing import Dict, List
from torch.utils.data import Dataset
from transformers import T5Tokenizer


class CompilerErrorDataset(Dataset):
    """Dataset for compiler error explanation."""
    
    def __init__(
        self,
        data_file: Path,
        tokenizer: T5Tokenizer,
        max_input_length: int = 512,
        max_output_length: int = 256
    ):
        """
        Initialize dataset.
        
        Args:
            data_file: Path to JSON file with data
            tokenizer: T5 tokenizer
            max_input_length: Maximum input sequence length
            max_output_length: Maximum output sequence length
        """
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_output_length = max_output_length
        
        # Load data
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, str]:
        """
        Get a single data sample.
        
        Args:
            idx: Sample index
            
        Returns:
            Dictionary with tokenized input and target
        """
        sample = self.data[idx]
        
        # Tokenize input
        input_text = sample['input']
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_input_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Tokenize target
        target_text = sample['target']
        target_encoding = self.tokenizer(
            target_text,
            max_length=self.max_output_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': input_encoding['input_ids'].squeeze(),
            'attention_mask': input_encoding['attention_mask'].squeeze(),
            'labels': target_encoding['input_ids'].squeeze()
        }

