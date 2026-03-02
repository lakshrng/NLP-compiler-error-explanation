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
         
    # Access Control
    (r"is private within this context", "Semantic Error: Private Member Access"),
    (r"is protected within this context", "Semantic Error: Protected Member Access"),
    (r"is inaccessible within this context", "Semantic Error: Inaccessible Member"),

    # Function Matching
    (r"no matching function for call to", "Semantic Error: No Matching Function"),
    (r"no matching member function for call to", "Semantic Error: No Matching Member Function"),

    # Ambiguity
    (r"call of overloaded .* is ambiguous", "Semantic Error: Ambiguous Function Call"),
    (r"reference to .* is ambiguous", "Semantic Error: Ambiguous Reference"),

    # Operator Errors
    (r"no match for .*operator", "Semantic Error: Operator Overload Failure"),
    (r"invalid operands of types .* to binary", "Type Error: Invalid Operator Operands"),

    # Templates
    (r"wrong number of template arguments", "Template Error: Incorrect Template Arguments"),
    (r"deduced conflicting types for parameter", "Template Error: Type Deduction Conflict"),
    (r"constraints not satisfied", "Template Error: Constraints Not Satisfied"),
    (r"unexpanded parameter pack", "Template Error: Unexpanded Parameter Pack"),

    # Deleted functions
    (r"use of deleted function", "Semantic Error: Deleted Function Usage"),

    # Abstract class
    (r"abstract type", "Semantic Error: Abstract Class Instantiation"),

    # Cast errors
    (r"invalid static_cast", "Type Error: Invalid Static Cast"),
    (r"reinterpret_cast .* is not allowed", "Type Error: Invalid Reinterpret Cast"),
    (r"cannot dynamic_cast", "Type Error: Invalid Dynamic Cast"),
    (r"casts away qualifiers", "Type Error: Casting Away Const"),

    # Static assert
    (r"static assertion failed", "Semantic Error: Static Assertion Failure"),

    # Namespace
    (r"has not been declared", "Semantic Error: Undeclared Namespace or Identifier"),

    # Read-only
    (r"assignment of read-only", "Semantic Error: Assignment to Read-Only Variable"),

    # Bit-field
    (r"cannot take address of bit-field", "Semantic Error: Address of Bit-field"),

    # Pointer arithmetic
    (r"arithmetic on pointer to an incomplete type", "Type Error: Invalid Pointer Arithmetic"),

    # Deprecated / Attributes
    (r"unknown attribute", "Attribute Warning: Unknown Attribute"),
    (r"is deprecated", "Attribute Warning: Deprecated Function"),
    (r"nodiscard", "Attribute Warning: Ignored Nodiscard Result"),
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
            },
                        "Semantic Error: Private Member Access": {
                "reason": "A private class member is being accessed from outside its allowed scope.",
                "fix": "Make the member public or access it through a public method."
            },

            "Semantic Error: Protected Member Access": {
                "reason": "A protected member is accessed from outside the class or its derived classes.",
                "fix": "Access the member within a derived class or change its access specifier."
            },

            "Semantic Error: Inaccessible Member": {
                "reason": "The base class member is inaccessible due to inheritance rules.",
                "fix": "Check inheritance visibility or modify access specifiers."
            },

            "Semantic Error: No Matching Function": {
                "reason": "No function overload matches the given arguments.",
                "fix": "Check argument types and ensure a compatible function signature exists."
            },

            "Semantic Error: Ambiguous Function Call": {
                "reason": "Multiple overloaded functions match the call equally well.",
                "fix": "Use explicit casting or specify arguments to remove ambiguity."
            },

            "Semantic Error: Operator Overload Failure": {
                "reason": "The required operator is not defined for the given operand types.",
                "fix": "Define the appropriate operator overload or use compatible types."
            },

            "Template Error: Incorrect Template Arguments": {
                "reason": "The number of template parameters provided does not match the template definition.",
                "fix": "Provide the correct number of template arguments."
            },

            "Template Error: Type Deduction Conflict": {
                "reason": "Template parameter types could not be deduced consistently.",
                "fix": "Ensure all template arguments resolve to the same type."
            },

            "Template Error: Constraints Not Satisfied": {
                "reason": "The template constraints are not satisfied for the provided type.",
                "fix": "Ensure the type meets the template's concept requirements."
            },

            "Semantic Error: Deleted Function Usage": {
                "reason": "A function marked as deleted is being called.",
                "fix": "Avoid calling deleted functions or provide a valid overload."
            },

            "Semantic Error: Abstract Class Instantiation": {
                "reason": "An abstract class with pure virtual functions cannot be instantiated.",
                "fix": "Implement all pure virtual functions or instantiate a concrete derived class."
            },

            "Type Error: Invalid Static Cast": {
                "reason": "An invalid static_cast operation was attempted.",
                "fix": "Ensure the cast is valid between related types."
            },

            "Semantic Error: Static Assertion Failure": {
                "reason": "A static_assert condition evaluated to false.",
                "fix": "Modify the condition or provide a type that satisfies the assertion."
            },

            "Semantic Error: Assignment to Read-Only Variable": {
                "reason": "An attempt was made to modify a const or read-only variable.",
                "fix": "Remove const qualifier or avoid modifying read-only data."
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