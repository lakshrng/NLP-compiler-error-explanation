"""Configuration management for the compiler error explanation system."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ModelConfig:
    """T5 model configuration."""
    model_name: str = "t5-small"
    max_input_length: int = 512
    max_output_length: int = 256
    num_train_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 3e-4
    warmup_steps: int = 500
    weight_decay: float = 0.01
    gradient_accumulation_steps: int = 1
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100


@dataclass
class DataConfig:
    """Data processing configuration."""
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    train_file: Path = Path("data/processed/train.json")
    val_file: Path = Path("data/processed/val.json")
    test_file: Path = Path("data/processed/test.json")
    max_samples: Optional[int] = None
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1


@dataclass
class TrainingConfig:
    """Training configuration."""
    output_dir: Path = Path("experiments/t5_small")
    seed: int = 42
    fp16: bool = False
    dataloader_num_workers: int = 4
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "rouge_l"
    greater_is_better: bool = True


@dataclass
class Config:
    """Main configuration class."""
    model: ModelConfig = ModelConfig()
    data: DataConfig = DataConfig()
    training: TrainingConfig = TrainingConfig()
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.data.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.data.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.training.output_dir.mkdir(parents=True, exist_ok=True)

