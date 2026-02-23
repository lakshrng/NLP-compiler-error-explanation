import re
import json


class RuleBasedExplainer:
    def __init__(self):
        self.total_predictions = 0
        self.matched_predictions = 0

        # -------------------------
        # REGEX CLASSIFICATION RULES
        # -------------------------
        self.rules = [
    # ODR / Redefinition
    (r"redefinition of", "Semantic Error: One Definition Rule Violation"),

    # Linkage
    (r"has both .*static.*extern", "Semantic Error: Conflicting Linkage Specifiers"),

    # Preprocessor
    (r"#endif without #if", "Preprocessor Error: Unbalanced Preprocessor Directive"),
    (r"unterminated #if", "Preprocessor Error: Unbalanced Preprocessor Directive"),

    # Include
    (r"missing terminating >", "Syntax Error: Incomplete Include Directive"),

    # Undeclared identifiers
    (r"was not declared in this scope", "Semantic Error: Undeclared Identifier"),
    (r"does not name a type", "Semantic Error: Undeclared Type"),

    # Missing semicolon
    (r"expected .*;.* before", "Syntax Error: Missing Semicolon"),

    # Linker
    (r"undefined reference to", "Linker Error: Undefined Reference"),

    # Type conversions
    (r"cannot convert .* to", "Type Error: Invalid Type Conversion"),
    (r"invalid conversion from", "Type Error: Invalid Type Conversion"),

    # Array assignment
    (r"assigning to an array from an initializer list", 
     "Type Error: Invalid Array Assignment"),

    # Void pointer misuse
    (r"is not a pointer-to-object type", 
     "Type Error: Invalid Pointer Dereference"),

    # Lvalue error
    (r"lvalue required as left operand of assignment",
     "Semantic Error: Invalid Assignment Target"),

    # Constexpr
    (r"is not a constant expression",
     "Semantic Error: Non-Constant Expression in Constexpr"),
]

        # -------------------------
        # EXPLANATION TEMPLATES
        # -------------------------
        self.templates = {
            "Semantic Error: One Definition Rule Violation": {
                "reason": "A function or variable is defined more than once, violating C++'s One Definition Rule (ODR).",
                "fix": "Ensure only one definition exists across translation units, or properly mark the function inline."
            },
            "Semantic Error: Conflicting Linkage Specifiers": {
                "reason": "A variable cannot simultaneously have internal linkage (static) and external linkage (extern).",
                "fix": "Remove either the static or extern specifier to ensure consistent linkage."
            },
            "Preprocessor Error: Unbalanced Preprocessor Directive": {
                "reason": "A preprocessor conditional (#if/#ifdef) is not properly matched with a corresponding #endif.",
                "fix": "Ensure every #if, #ifdef, or #ifndef has a matching #endif."
            },
            "Syntax Error: Incomplete Include Directive": {
                "reason": "The #include directive is missing a closing '>' character.",
                "fix": "Add the missing '>' to properly close the include directive."
            },
            "Semantic Error: Undeclared Identifier": {
                "reason": "The identifier is used without being declared in the current scope.",
                "fix": "Declare the variable or include the appropriate header before use."
            },
            "Syntax Error: Missing Semicolon": {
                "reason": "A statement is missing a terminating semicolon.",
                "fix": "Add a semicolon at the end of the statement."
            },
            "Linker Error: Undefined Reference": {
                "reason": "The linker cannot find the definition of a referenced function or variable.",
                "fix": "Ensure the function or variable is properly defined and linked during compilation."
            },
            "Type Error: Type Mismatch": {
                "reason": "An expression attempts to convert between incompatible types.",
                "fix": "Ensure the types are compatible or use explicit casting if appropriate."
            },
            "Type Error: Invalid Type Conversion": {
                "reason": "An invalid implicit conversion between types was attempted.",
                "fix": "Use explicit casting or correct the type usage."
            },
            "Semantic Error: Non-Constant Expression in Constexpr": {
                "reason": "A constexpr context requires compile-time constant expressions.",
                "fix": "Ensure all expressions in constexpr evaluation are compile-time constants."
            },

            "Type Error: Invalid Array Assignment": {
                "reason": "An array cannot be assigned using an initializer list after it has already been declared.",
                "fix": "Initialize the array at declaration time, or use std::array or std::vector if reassignment is required."
            },

            "Type Error: Invalid Pointer Dereference": {
                "reason": "A void pointer (void*) does not have a concrete type and cannot be directly dereferenced.",
                "fix": "Cast the void pointer to the appropriate pointer type before dereferencing."
            },

            "Semantic Error: Invalid Assignment Target": {
                "reason": "The left-hand side of an assignment must be a modifiable lvalue.",
                "fix": "Ensure the assignment target is a valid variable and not a temporary value or an expression like '&x'."
            }
        }

    # -------------------------
    # Extract compiler message
    # -------------------------
    def extract_error_message(self, full_input):
        match = re.search(r"(error:.*|warning:.*)", full_input, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return full_input.strip()

    # -------------------------
    # Classification
    # -------------------------
    # def classify(self, full_input):
    #     self.total_predictions += 1

    #     error_msg = self.extract_error_message(full_input)

    #     for pattern, label in self.rules:
    #         if re.search(pattern, error_msg, re.IGNORECASE):
    #             self.matched_predictions += 1
    #             return label

    #     return "Unknown Error"
    def classify(self, full_input):
        self.total_predictions += 1

        print("\nFULL INPUT:\n", full_input)

        for pattern, label in self.rules:
            if re.search(pattern, full_input, re.IGNORECASE):
                print("MATCHED PATTERN:", pattern)
                self.matched_predictions += 1
                return label

        print("NO MATCH FOUND")
        return "Unknown Error"
    # -------------------------
    # Explanation
    # -------------------------
    def explain(self, full_input):
        label = self.classify(full_input)
        error_msg = self.extract_error_message(full_input)

        if label in self.templates:
            template = self.templates[label]
            return f"""The compiler reports: {error_msg}

Category: {label}

Reason:
{template['reason']}

Fix:
{template['fix']}
"""
        else:
            return f"""The compiler reports: {error_msg}

Category: Unknown Error

Reason:
No predefined rule matched this compiler diagnostic.

Fix:
Review the compiler message and update the rule-based system if necessary.
"""

    # -------------------------
    # Coverage Metric
    # -------------------------
    def coverage(self):
        if self.total_predictions == 0:
            return 0
        return self.matched_predictions / self.total_predictions