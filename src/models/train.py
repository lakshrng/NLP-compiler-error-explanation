"""Training script for T5 model."""
import os
from pathlib import Path
import torch
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq
)
from torch.utils.data import DataLoader
from src.data.dataset import CompilerErrorDataset
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger()


def train_model(config: Config):
    """
    Train T5 model on compiler error explanation data.
    
    Args:
        config: Configuration object
    """
    logger.info("Starting model training")
    
    # Load model and tokenizer
    tokenizer = T5Tokenizer.from_pretrained(config.model.model_name)
    model = T5ForConditionalGeneration.from_pretrained(config.model.model_name)
    
    # Load datasets
    train_dataset = CompilerErrorDataset(
        config.data.train_file,
        tokenizer,
        config.model.max_input_length,
        config.model.max_output_length
    )
    
    val_dataset = CompilerErrorDataset(
        config.data.val_file,
        tokenizer,
        config.model.max_input_length,
        config.model.max_output_length
    )
    
    logger.info(f"Train dataset size: {len(train_dataset)}")
    logger.info(f"Validation dataset size: {len(val_dataset)}")
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(config.training.output_dir),
        num_train_epochs=config.model.num_train_epochs,
        per_device_train_batch_size=config.model.batch_size,
        per_device_eval_batch_size=config.model.batch_size,
        learning_rate=config.model.learning_rate,
        warmup_steps=config.model.warmup_steps,
        weight_decay=config.model.weight_decay,
        gradient_accumulation_steps=config.model.gradient_accumulation_steps,
        logging_steps=config.model.logging_steps,
        save_steps=config.model.save_steps,
        eval_steps=config.model.eval_steps,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=config.training.load_best_model_at_end,
        metric_for_best_model=config.training.metric_for_best_model,
        greater_is_better=config.training.greater_is_better,
        fp16=config.training.fp16,
        dataloader_num_workers=config.training.dataloader_num_workers,
        seed=config.training.seed,
        report_to="none"  # Disable wandb/tensorboard by default
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer
    )
    
    # Train
    logger.info("Starting training...")
    trainer.train()
    
    # Save final model
    final_model_dir = config.training.output_dir / "final_model"
    trainer.save_model(str(final_model_dir))
    tokenizer.save_pretrained(str(final_model_dir))
    logger.info(f"Model saved to {final_model_dir}")
    
    logger.info("Training completed")

