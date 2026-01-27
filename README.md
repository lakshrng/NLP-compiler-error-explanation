# Compiler Error Explanation System

A deep learning system for automatically explaining compiler errors using T5 (Text-to-Text Transfer Transformer) models.

## Project Structure

```
compiler-error-explainer/
├── data/
│   ├── raw/                    # Raw error data files
│   │   ├── gcc_errors.txt
│   │   ├── clang_errors.txt
│   │   └── explanations.txt
│   ├── processed/              # Processed datasets
│   │   ├── train.json
│   │   ├── val.json
│   │   └── test.json
│   └── rules/
│       └── rule_based_errors.json
├── src/
│   ├── data/                   # Data processing modules
│   │   ├── collect_errors.py
│   │   ├── preprocess.py
│   │   └── dataset.py
│   ├── models/                 # Model implementation
│   │   ├── t5_model.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   ├── baseline/               # Baseline methods
│   │   └── rule_based.py
│   ├── utils/                  # Utility modules
│   │   ├── metrics.py
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                 # Main entry point
├── experiments/                # Experiment results
│   ├── t5_small/
│   │   ├── config.yaml
│   │   └── results.txt
│   └── bart/
│       └── notes.txt
├── demo/                       # Demo applications
│   ├── cli_demo.py
│   └── sample_errors.txt
├── requirements.txt
├── README.md
└── report/                     # Project reports
    ├── proposal.pdf
    ├── mid_review.pdf
    └── final_report.pdf
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download NLTK Data

The evaluation metrics require NLTK data. Run the following Python command:

```python
import nltk
nltk.download('punkt')
```

Or from command line:

```bash
python -c "import nltk; nltk.download('punkt')"
```

### Step 3: Prepare Data

Place your compiler error data in the `data/raw/` directory. The data should be formatted as alternating lines:
- Line 1: Error message
- Line 2: Explanation
- Line 3: Error message
- Line 4: Explanation
- ...

Example format for `data/raw/gcc_errors.txt`:
```
error: 'printf' was not declared in this scope
This error occurs when you use printf without including <stdio.h> header file.
error: expected ';' before '}' token
This error indicates a missing semicolon before a closing brace.
```

## Usage

### 1. Preprocess Data

Convert raw data into training format:

```bash
python src/main.py --mode preprocess
```

This creates `train.json`, `val.json`, and `test.json` in `data/processed/`.

### 2. Train Model

Train the T5-small model:

```bash
python src/main.py --mode train
```

The model will be saved in `experiments/t5_small/final_model/`.

### 3. Evaluate Model

Evaluate the trained model on test data:

```bash
python src/main.py --mode evaluate --model-path experiments/t5_small/final_model
```

### 4. Run Inference

Explain a single compiler error:

```bash
python src/main.py --mode inference --error "error: 'printf' was not declared in this scope" --model-path experiments/t5_small/final_model
```

### 5. Interactive Demo

Run the interactive CLI demo:

```bash
python demo/cli_demo.py --model-path experiments/t5_small/final_model
```

Or without a trained model (uses base T5-small):

```bash
python demo/cli_demo.py
```

## Configuration

Modify `src/utils/config.py` to adjust:
- Model parameters (learning rate, batch size, epochs, etc.)
- Data paths
- Training settings

## Key Files

### Immediately Required Files for T5 Small Model

1. **Core Data Processing:**
   - `src/data/preprocess.py` - Data preprocessing
   - `src/data/dataset.py` - PyTorch dataset class

2. **Model Implementation:**
   - `src/models/t5_model.py` - Model loading utilities
   - `src/models/train.py` - Training script
   - `src/models/evaluate.py` - Evaluation script
   - `src/models/inference.py` - Inference interface

3. **Utilities:**
   - `src/utils/config.py` - Configuration management
   - `src/utils/logger.py` - Logging utilities
   - `src/utils/metrics.py` - Evaluation metrics (ROUGE, BLEU)

4. **Entry Points:**
   - `src/main.py` - Main CLI interface
   - `demo/cli_demo.py` - Interactive demo

5. **Configuration:**
   - `requirements.txt` - Python dependencies
   - `README.md` - Documentation

## Dependencies

- **torch**: PyTorch deep learning framework
- **transformers**: Hugging Face Transformers library (T5 models)
- **datasets**: Dataset utilities
- **rouge-score**: ROUGE metric for evaluation
- **nltk**: Natural Language Toolkit (for BLEU metric)
- **numpy**: Numerical computing
- **tqdm**: Progress bars

## Notes

- The system uses T5-small by default, which is a relatively lightweight model suitable for experimentation
- Training requires GPU for reasonable speed (CPU training is possible but very slow)
- The model expects error messages in the format: `"explain compiler error: <error_message>"`
- Evaluation metrics include ROUGE-1, ROUGE-2, ROUGE-L, and BLEU scores

## Troubleshooting

1. **Import errors**: Make sure you're running commands from the project root directory
2. **CUDA errors**: If you don't have a GPU, the model will use CPU (slower)
3. **Data format errors**: Ensure your raw data files follow the alternating line format
4. **Memory errors**: Reduce batch size in `config.py` if you run out of memory

