from datasets import load_from_disk
from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers import TrainingArguments, Trainer
import os
import torch

# Paths
DATA_PATH = "data/processed/tokenized/t5_small_explain"
MODEL_NAME = "t5-small"
OUTPUT_DIR = "models/checkpoints/test"

print("Loading data...")
try:
    train_dataset = load_from_disk(f"{DATA_PATH}/train")
    val_dataset = load_from_disk(f"{DATA_PATH}/validation")
    print(f"Loaded {len(train_dataset)} train samples and {len(val_dataset)} val samples.")
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

print("Loading model...")
tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

# Training arguments - VERY minimal
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    max_steps=5, # Just 5 steps
    per_device_train_batch_size=1, # Tiny batch
    report_to="none",
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

print("Starting test train...")
try:
    trainer.train()
    print("Test train successful!")
except Exception as e:
    print(f"Training failed: {e}")
    import traceback
    traceback.print_exc()
