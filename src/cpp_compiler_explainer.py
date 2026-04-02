import subprocess
import sys
import re
from pathlib import Path

# Add project root so "src" is importable
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.hybrid_explainer import HybridExplainer
from src.utils.logger import setup_logger

logger = setup_logger()

class CPPCompilerExplainer:
    def __init__(self, model_path: Path = None):
        self.explainer = HybridExplainer(model_path=model_path)
    
    def compile_and_explain(self, file_path: Path):
        """
        Compiles the given C++ file and explains any errors.
        """
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return

        # Read the code
        with open(file_path, 'r') as f:
            code = f.read()

        # Run g++ to check for errors
        # -fsyntax-only: check for errors but don't produce any output
        # -fdiagnostics-color=never: get plain text output
        # -pedantic-errors: treat warnings about ISO C++ as errors
        result = subprocess.run(
            ["g++", "-fsyntax-only", "-fdiagnostics-color=never", "-pedantic-errors", str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("Compilation successful! No errors found.")
            return

        stderr = result.stderr
        print("\n--- Compiler Output ---\n")
        print(stderr)

        # Parse errors
        # Errors usually look like: file:line:col: error: message
        # We'll try to find each line that contains "error:" or "warning:"
        
        errors = self.parse_errors(stderr)
        
        if not errors:
            print("No specific error messages could be parsed.")
            return

        print("\n--- Hybrid Explanation ---\n")
        for i, err_msg in enumerate(errors, 1):
            print(f"--- Error {i} ---")
            # We'll pass both the code and the error message to the explainer
            # But the current explainer only takes error_message.
            # I'll modify the explainer's explain() method later if needed.
            
            # For now, let's construct the input as expected by the model
            # "explain_error: C++ code:\n{code}\nCompiler output:\n{error_msg}"
            
            full_input = f"explain_error: C++ code:\n{code}\nCompiler output:\n{err_msg}"
            explanation = self.explainer.explain(full_input)
            print(explanation)
            print("-" * 20)

    def parse_errors(self, stderr):
        """
        Parses stderr to find distinct error messages.
        """
        lines = stderr.splitlines()
        errors = []
        
        # This is a very simple parser. 
        # A more robust one would handle multi-line errors.
        # Often, g++ outputs:
        # file:line:col: error: message
        #    code snippet
        #    ^ pointer
        
        # We'll look for lines containing " error: " or " warning: "
        for line in lines:
            if " error: " in line or " warning: " in line:
                # Extract the part after the last colon which is the actual error message
                # file:line:col: error: message -> error: message
                match = re.search(r"(error:.*|warning:.*)", line, re.IGNORECASE)
                if match:
                    errors.append(match.group(1).strip())
        
        return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Explain C++ Compiler Errors")
    parser.add_argument('file', type=str, help="C++ source file")
    parser.add_argument('--model-path', type=str, default="models/final_t5_model", help="Path to trained T5 model")
    
    args = parser.parse_args()
    
    model_path = Path(args.model_path)
    explainer = CPPCompilerExplainer(model_path=model_path)
    explainer.compile_and_explain(Path(args.file))
