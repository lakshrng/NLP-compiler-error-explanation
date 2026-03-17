from datasets import load_from_disk
from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers import TrainingArguments, Trainer
import os

# Paths
DATA_PATH = "data/processed/tokenized/t5_small"
MODEL_NAME = "t5-small"
OUTPUT_DIR = "models/checkpoints/t5_small"

# Load datasets
train_dataset = load_from_disk(f"{DATA_PATH}/train")
val_dataset = load_from_disk(f"{DATA_PATH}/validation")

# Load tokenizer and model
tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    learning_rate=3e-4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="logs",
    logging_steps=50,
    save_total_limit=2,
    save_strategy="epoch",
    load_best_model_at_end=True,

     report_to="tensorboard", 
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
)

# Train
trainer.train()

# Save final model
trainer.save_model("models/final_t5_model")
tokenizer.save_pretrained("models/final_t5_model")

print("Training complete. Model saved.")