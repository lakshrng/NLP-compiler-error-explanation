"""Prepare tokenized HuggingFace datasets for T5-small training."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from datasets import DatasetDict, load_dataset
from transformers import AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.logger import setup_logger

MODEL_NAME = "t5-small"
MAX_INPUT_LENGTH = 256
MAX_TARGET_LENGTH = 128

DATA_DIR = REPO_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TOKENIZED_OUTPUT_DIR = PROCESSED_DATA_DIR / "tokenized" / "t5_small"

logger = setup_logger()


def resolve_split_path(split_name: str) -> Path | None:
    """Return the first existing path for a dataset split."""
    candidate_paths = [
        DATA_DIR / f"{split_name}.json",
        PROCESSED_DATA_DIR / f"{split_name}.json",
    ]

    for candidate_path in candidate_paths:
        if candidate_path.exists():
            return candidate_path

    return None


def collect_data_files() -> dict[str, str]:
    """Collect available train/validation/test files without recreating data."""
    split_aliases = {
        "train": "train",
        "validation": "val",
        "test": "test",
    }

    data_files: dict[str, str] = {}
    for split_name, file_stem in split_aliases.items():
        split_path = resolve_split_path(file_stem)
        if split_path is None:
            if split_name == "train":
                raise FileNotFoundError(
                    "Could not find training data at 'data/train.json' "
                    "or 'data/processed/train.json'."
                )
            continue

        data_files[split_name] = str(split_path)

    return data_files


def load_raw_datasets() -> DatasetDict:
    """Load JSON datasets using the HuggingFace datasets library."""
    data_files = collect_data_files()
    logger.info("Loading dataset files: %s", data_files)

    raw_datasets = load_dataset("json", data_files=data_files)
    logger.info("Loaded dataset splits: %s", list(raw_datasets.keys()))
    return raw_datasets


def build_tokenizer() -> Any:
    """Initialize the T5-small tokenizer with SentencePiece support."""
    logger.info("Loading tokenizer for %s", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    logger.info("Tokenizer loaded successfully")
    return tokenizer


def preprocess_batch(examples: dict[str, list[str]], tokenizer: Any) -> dict[str, list[list[int]]]:
    """Tokenize multitask input/target pairs for T5 training."""
    model_inputs = tokenizer(
        examples["input"],
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
        padding="max_length",
    )

    if "target" not in examples:
        return model_inputs

    tokenized_targets = tokenizer(
        text_target=examples["target"],
        max_length=MAX_TARGET_LENGTH,
        truncation=True,
        padding="max_length",
    )

    labels = []
    for label_ids in tokenized_targets["input_ids"]:
        labels.append([
            token_id if token_id != tokenizer.pad_token_id else -100
            for token_id in label_ids
        ])

    model_inputs["labels"] = labels
    return model_inputs


def tokenize_datasets(raw_datasets: DatasetDict, tokenizer: Any) -> DatasetDict:
    """Apply batched tokenization across all available dataset splits."""
    sample_split_name = next(iter(raw_datasets.keys()))
    columns_to_remove = raw_datasets[sample_split_name].column_names

    tokenized_datasets = raw_datasets.map(
        lambda batch: preprocess_batch(batch, tokenizer),
        batched=True,
        remove_columns=columns_to_remove,
        desc="Tokenizing dataset",
    )

    return tokenized_datasets


def print_dataset_summary(tokenized_datasets: DatasetDict) -> None:
    """Print a compact dataset summary for quick verification."""
    print("\nTokenized dataset summary")
    print(tokenized_datasets)

    for split_name, split_dataset in tokenized_datasets.items():
        first_row = split_dataset[0]
        print(f"\nSplit: {split_name}")
        print(f"Rows: {len(split_dataset)}")
        print(f"Columns: {list(split_dataset.features.keys())}")
        print(f"Input length: {len(first_row['input_ids'])}")
        print(f"Attention length: {len(first_row['attention_mask'])}")
        if "labels" in first_row:
            print(f"Label length: {len(first_row['labels'])}")


def save_tokenized_datasets(tokenized_datasets: DatasetDict) -> Path:
    """Persist the tokenized dataset for the upcoming training step."""
    TOKENIZED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tokenized_datasets.save_to_disk(str(TOKENIZED_OUTPUT_DIR))
    logger.info("Saved tokenized dataset to %s", TOKENIZED_OUTPUT_DIR)
    return TOKENIZED_OUTPUT_DIR


def main() -> None:
    """Run the full dataset loading and tokenization pipeline."""
    raw_datasets = load_raw_datasets()
    tokenizer = build_tokenizer()
    tokenized_datasets = tokenize_datasets(raw_datasets, tokenizer)
    output_dir = save_tokenized_datasets(tokenized_datasets)
    print_dataset_summary(tokenized_datasets)
    print(f"\nSaved tokenized dataset to: {output_dir}")


if __name__ == "__main__":
    main()
