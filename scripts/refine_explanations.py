"""
Refine explain_error targets in train.json: replace weak explanations with
high-quality, human-readable ones. No classification leakage; 3-5 sentences;
cause, rule, fix.
"""
import json
import re
from pathlib import Path
from typing import Optional


def parse_explain_input(inp: str) -> tuple[str, str]:
    """Extract code and compiler output from explain_error input."""
    prefix = "explain_error: "
    if not inp.startswith(prefix):
        return "", ""
    body = inp[len(prefix) :]
    if "Compiler output:" in body:
        code_part, out_part = body.split("Compiler output:", 1)
        code = code_part.replace("C++ code:\n", "", 1).strip()
        return code, out_part.strip()
    return body.strip(), ""


def extract_identifier(msg: str, pattern: str) -> str:
    """Extract first quoted or backticked identifier from message."""
    m = re.search(pattern, msg)
    return m.group(1) if m else ""


def _quoted_identifier(msg: str) -> str:
    """Get first identifier in single quotes (straight or curly), e.g. 'count' from \"'count' was not declared\"."""
    m = re.search(r"['\u2018\u2019]([^'\u2018\u2019]+)['\u2018\u2019]", msg)
    return m.group(1).strip() if m else ""


def generate_explanation(code: str, compiler_output: str) -> str:
    """
    Generate 3-5 sentence explanation: cause, violated rule, how to fix.
    No classification wording (no "Semantic Error", "Syntax Error", "classified", "compiler reports").
    """
    msg = compiler_output
    first = msg.split("\n")[0]

    # Type mismatch / conversion errors
    if "cannot convert" in first or "invalid conversion" in first or "conversion from" in first:
        return (
            "A value is being used where a different type is required. "
            "C++ does not allow implicit conversion between incompatible types such as pointers and integers, or between unrelated class types. "
            "Use an explicit cast only when the conversion is well-defined and safe, or change the variable or argument type to match the value you are providing."
        )
    if "narrowing conversion" in first or "narrowing" in first:
        return (
            "A narrowing conversion is attempted in a context that forbids it (e.g. brace initialization). "
            "C++ brace-initialization disallows implicit narrowing from a larger or floating-point type to a smaller or integer type. "
            "Use an explicit cast if the loss of precision is intended, or initialize with a value that fits the target type."
        )

    # Unbalanced parentheses: expected ')' before ';' (must be before generic semicolon)
    if "expected" in first and ")" in first and "before" in first and ";" in first and "}" not in first:
        return (
            "An opening parenthesis is not matched by a closing one before a semicolon. "
            "Every opening parenthesis must have a matching closing parenthesis in the correct place. "
            "Add the missing closing parenthesis or remove the extra opening one."
        )

    # Missing semicolon
    if "expected" in first and ";" in first:
        if "before" in first and "}" in first:
            return (
                "A statement is missing a semicolon before a closing brace. "
                "In C++, every statement must end with a semicolon. "
                "Add a semicolon after the last statement inside the block (e.g. after return or the last declaration)."
            )
        if "after struct" in first or "after class" in first:
            return (
                "A struct or class definition is missing a semicolon after the closing brace. "
                "In C++, type definitions end with a semicolon after the closing brace. "
                "Add a semicolon immediately after the closing brace of the struct or class."
            )
        if "after " in first and "while" in first:
            return (
                "The do-while loop is missing a semicolon after the condition. "
                "In C++, the form is do { } while (condition); with a semicolon after the closing parenthesis. "
                "Add a semicolon after the closing parenthesis of the while condition."
            )
        if "before ')'" in first:
            return (
                "A semicolon appears where the parser expects a closing parenthesis, or a parenthesis is missing. "
                "Check that every opening parenthesis has a matching closing one and that expressions are not terminated by a semicolon too early. "
                "Fix the parentheses and remove or move any misplaced semicolon."
            )
        return (
            "The parser expected a semicolon at this location. "
            "In C++, statements and declarations end with a semicolon. "
            "Add the missing semicolon where the compiler indicates."
        )

    if "expected ')' at end" in first or "')' at end of input" in first:
        return (
            "The compiler reached the end of the file or a construct while still expecting a closing parenthesis. "
            "This often happens when a macro or expression is missing a closing parenthesis. "
            "Add the missing closing parenthesis in the macro definition or expression."
        )

    # Undeclared / not declared / scope
    if "was not declared" in first or "were not declared" in first:
        name = _quoted_identifier(first)
        hint = " did you mean " in first
        if hint or name:
            ident = f" '{name}'" if name else ""
            return (
                f"The name{ident} is used but has not been declared in this scope. "
                "In C++, every identifier must be declared before use. "
                "Declare the variable or function before using it, or fix the spelling if the compiler suggests an alternative."
            )
        return (
            "An identifier is used in a scope where it is not visible. "
            "In C++, variables and functions must be declared before use and are only visible within their scope. "
            "Move the declaration above the use, or ensure the name is in scope (e.g. correct namespace or block)."
        )
    if "has not been declared" in first:
        return (
            "A name is used in a context where it has not been declared. "
            "C++ requires declarations (or includes that provide them) before use. "
            "Add the appropriate declaration or include, or fix the scope or spelling of the name."
        )

    # Redeclaration / redefinition
    if "conflicting declaration" in first:
        return (
            "The same name is declared more than once with different types in the same scope. "
            "C++ does not allow two declarations of the same variable with incompatible types in one scope. "
            "Use a single declaration with the correct type, or use a different name for one of the variables."
        )
    if "redefinition of" in first:
        return (
            "A function or variable is defined more than once in a way that violates the one-definition rules. "
            "In C++, each function and non-inline variable must have exactly one definition in the program (within the same linkage). "
            "Keep a single definition, or make the function inline or put it in a header with proper include guards, as appropriate."
        )

    # const
    if "read-only" in first or "assignment of read-only" in first or "increment of read-only" in first:
        return (
            "An attempt is made to modify an object that is declared const or passed as a const reference. "
            "Const-qualified objects and references cannot be assigned to or modified. "
            "Remove the modification, or change the declaration to non-const if the object is meant to be mutable."
        )

    # Function arguments
    if "too few arguments" in first:
        return (
            "A function is called with fewer arguments than its declaration requires. "
            "In C++, the number and types of arguments must match the function declaration. "
            "Add the missing arguments in the call, or add default arguments to the function declaration if that is intended."
        )
    if "too many arguments" in first:
        return (
            "A function is called with more arguments than its declaration accepts. "
            "The call must match the declared parameter list. "
            "Remove the extra arguments or add corresponding parameters (possibly with defaults) to the function."
        )

    # Return
    if "return-statement with no value" in first and "returning 'int'" in first:
        return (
            "A return statement has no value in a function that is declared to return a type (e.g. int). "
            "Every return path in a non-void function must supply a value of the return type. "
            "Return an expression of the correct type, e.g. return 0; or return expr;."
        )
    if "return-statement with a value" in first and "returning 'void'" in first:
        return (
            "A return statement provides a value in a function declared to return void. "
            "Void functions must not return a value. "
            "Use return; without an expression, or change the function return type if it should return a value."
        )

    # Access (private, protected, no member)
    if "is private" in first or "is protected" in first or "inaccessible" in first:
        return (
            "A class member is accessed from a context where it is not accessible. "
            "Private members are only accessible within the class and friends; protected within the class, derived classes, and friends. "
            "Use a public member or friend, or add a public accessor; do not bypass access rules."
        )
    if "has no member named" in first:
        return (
            "Code calls a member (data or function) that does not exist for that type. "
            "The name or signature may be wrong, or the member might be in a base class and not accessible. "
            "Fix the member name, add the member to the class, or use the correct type."
        )

    # Abstract
    if "cannot declare variable" in first and "abstract" in msg:
        return (
            "A variable is declared with an abstract class type. "
            "Abstract classes have at least one pure virtual function and cannot be instantiated. "
            "Use a pointer or reference to the abstract type and assign it a concrete derived object."
        )

    # Header / include
    if "No such file or directory" in first or "nonexistent" in first:
        return (
            "An included file cannot be found. "
            "#include directives must refer to an existing file in the include path. "
            "Check the file name and path, and ensure the header exists and the include path is set correctly."
        )
    if "missing terminating" in first and ">" in first:
        return (
            "An #include directive is missing the closing angle bracket. "
            "Standard headers are included with #include <filename>. "
            "Add the closing '>' to the #include line."
        )

    # Preprocessor / macro
    if "extra tokens at end of #define" in first:
        return (
            "A #define directive has extra tokens after the replacement list. "
            "Preprocessor macro definitions must end after the replacement list (or use a continuation line). "
            "Remove the extra tokens or move them into the replacement list if they are intended to be part of the macro."
        )
    if "#endif without #if" in first:
        return (
            "An #endif appears without a matching #if, #ifdef, or #ifndef. "
            "Preprocessor conditionals must be properly nested and matched. "
            "Ensure every #endif has a matching #if/#ifdef/#ifndef and that they are correctly nested."
        )
    if "expected ')' at end of input" in first and "#define" in code:
            return (
                "A macro is defined with unbalanced parentheses. When the macro is expanded, the parser reaches end of input still expecting a closing parenthesis. "
                "Macro definitions that use parentheses must have matching opening and closing parentheses. "
                "Add the missing closing parenthesis in the #define body."
            )

    # Switch / control flow
    if "switch quantity not an integer" in first:
        return (
            "The switch expression is not of an integer or enumeration type. "
            "In C++, the controlling expression of switch must have integral or enumeration type. "
            "Use an integer or enum expression, or convert the value explicitly (e.g. to int) if that is meaningful."
        )
    if "comparison between" in first and "and " in first:
        return (
            "Two values of incompatible types are compared with == or similar. "
            "C++ does not define comparison between certain types (e.g. pointer and integer, or unrelated pointers). "
            "Compare values of the same or comparable types, or use an explicit conversion if the comparison is intended and well-defined."
        )
    if "ordered comparison of pointer" in first:
        return (
            "Pointers are compared with <, >, <=, or >= in a way that is not allowed. "
            "Relational comparison of pointers is only valid when both point into the same array or object. "
            "Use == or != for equality, or ensure both pointers are in the same array before using relational comparison."
        )

    # For loop / do-while / else
    if "expected ';' before ')'" in first and "for" in code:
        return (
            "The for-loop is missing a semicolon in its header. "
            "A for statement has the form for (init; condition; increment) and requires two semicolons. "
            "Add the missing semicolon between the condition and the increment part (or between init and condition)."
        )
    if "'else' without a previous 'if'" in first:
        return (
            "An else clause appears without a matching if. "
            "In C++, else must immediately follow an if (or else if) block. "
            "Ensure the preceding if is not closed by a stray semicolon and that the else is attached to the correct if."
        )
    if "jump to case label crosses initialization" in first:
        return (
            "A switch case label is reached by jump (from another case or default) and would skip the initialization of a variable. "
            "C++ does not allow jumping over a declaration with initializer into the same block. "
            "Wrap the case in a block with braces so the variable is only in scope in that case, or move the declaration above the switch."
        )

    # References
    if "reference but not initialized" in first or "declared as reference but not initialized" in first:
        return (
            "A reference is declared without being bound to an object. "
            "In C++, every reference must be initialized when it is created. "
            "Initialize the reference with a valid object of the correct type in the same statement."
        )
    if "cannot bind non-const lvalue reference" in first and "rvalue" in first:
        return (
            "A non-const lvalue reference is being bound to a temporary or rvalue. "
            "Non-const lvalue references can only bind to modifiable lvalues. "
            "Use const int& to bind to a temporary, or bind to a named variable (lvalue)."
        )

    # new/delete / allocation
    if "mismatched" in first and "delete" in first or ("delete" in first and "new" in first):
        return (
            "Memory is freed with a deallocation function that does not match how it was allocated. "
            "Memory from new must be freed with delete; from new[] with delete[]; from malloc with free. "
            "Use the matching deallocation form, and do not mix C and C++ allocation."
        )
    if "'delete' applied to a pointer" in first or "allocated with" in first:
        return (
            "The pointer passed to delete was not allocated with the corresponding new form. "
            "new must be paired with delete; new[] with delete[]. "
            "Use delete for single objects and delete[] for arrays, and do not delete the same pointer twice."
        )
    if "variable length array" in first or "ISO C++ forbids variable length array" in first:
        return (
            "An array is declared with a size that is not a constant expression. "
            "In standard C++, array bounds must be compile-time constants. "
            "Use a constant size, or use std::vector (or another container) for a runtime size."
        )
    if "too many initializers" in first:
        return (
            "More initializers are provided than there are elements in the array or aggregate. "
            "The number of initializers must not exceed the size of the array or the number of members. "
            "Reduce the number of initializers or increase the array size."
        )
    if "zero-size array" in first:
        return (
            "An array is declared with size zero. "
            "C++ does not allow zero-length arrays. "
            "Use a positive constant size or a different container (e.g. std::vector)."
        )
    if "assigning to an array" in first or "from an initializer list" in first:
        return (
            "An attempt is made to assign to an array (e.g. with = { ... }). "
            "Arrays cannot be assigned to as a whole after initialization. "
            "Assign element by element, or use std::array or std::vector which support assignment."
        )

    # Pointers
    if "cannot convert" in first and "'int*'" in first and "'double*'" in first:
        return (
            "A pointer to one type is assigned to a pointer to an unrelated type. "
            "C++ does not allow implicit conversion between pointers to different object types. "
            "Use the correct pointer type, or use a proper cast (e.g. reinterpret_cast) only when the conversion is well-defined."
        )
    if "'void*' is not a pointer-to-object" in first or "dereferencing void" in first:
        return (
            "A void pointer is dereferenced or used in a way that requires a known object type. "
            "The size and type of the object pointed to by void* are unknown, so dereference is not allowed. "
            "Cast the void* to a pointer to the correct type before dereferencing."
        )
    if "lvalue required as left operand" in first:
        return (
            "The left side of an assignment is not an lvalue (a modifiable location). "
            "Only lvalues (variables, dereferenced pointers, etc.) can be assigned to. "
            "Assign to a variable or a valid lvalue, not to a temporary or the result of an expression."
        )
    if "dereferencing NULL pointer" in first or "dereferencing a released" in first:
        return (
            "A null or released pointer is dereferenced. "
            "Dereferencing a null or invalid pointer is undefined behavior. "
            "Check that the pointer is non-null and valid before dereferencing, and do not use it after release or delete."
        )
    if "type 'int' argument given to 'delete'" in first or "expected pointer" in first:
        return (
            "The operand of delete is not a pointer. "
            "Delete must be applied to a pointer previously returned by new. "
            "Pass a pointer value to delete, and do not delete the same pointer twice."
        )
    if "'free' called on pointer allocated with 'new'" in first or "allocated with 'new'" in first:
        return (
            "Memory allocated with C++ new is being freed with C free. "
            "C++ and C allocation must not be mixed: new with delete, malloc with free. "
            "Use delete (or delete[]) for memory from new."
        )

    # Class / member access
    if "is private within this context" in first or "is protected within this context" in first:
        return (
            "A member is accessed from outside its allowed context. "
            "Private and protected members are not accessible from arbitrary code. "
            "Use a public member or interface, or add a friend declaration or accessor if appropriate."
        )

    # Double free / smart pointers
    if "raw pointer owned by 'shared_ptr'" in first or "'delete' called on raw pointer" in first:
        return (
            "A raw pointer obtained from a smart pointer (e.g. get()) is passed to delete. "
            "The smart pointer already owns the object and will delete it; manual delete causes double free. "
            "Do not delete the result of get(); let the smart pointer manage lifetime."
        )

    # auto
    if "declaration of 'auto" in first and "has no initializer" in first:
        return (
            "A variable declared with auto has no initializer. "
            "The type of an auto variable is deduced from its initializer, so one must be provided. "
            "Initialize the variable in the declaration, e.g. auto x = 5;"
        )

    # constexpr
    if "call to non-constexpr function" in first:
        return (
            "A constexpr variable or constant expression calls a function that is not constexpr. "
            "Constexpr evaluation requires the expression to involve only constexpr functions and constant operands. "
            "Make the called function constexpr if possible, or do not use it in a constexpr context."
        )
    if "not usable in a constant expression" in first:
        return (
            "A value that is not constant is used where a constant expression is required. "
            "Constexpr and template arguments require compile-time constant values. "
            "Use a literal or constexpr value, or move the computation out of the constant expression context."
        )

    # Iterators / containers
    if "cannot convert 'const char*' to 'int' in assignment" in first and "iterator" in msg.lower():
        return (
            "A value of the wrong type is assigned through an iterator (e.g. to a vector<int> element). "
            "The iterator's element type is fixed by the container. "
            "Assign a value of the container's element type (e.g. int for vector<int>)."
        )
    if "no match for 'operator<'" in first and "Point" in first:
        return (
            "A standard algorithm (e.g. std::sort) requires operator< for the element type, but it is not defined. "
            "Sorting and other comparisons need a way to compare two elements. "
            "Define operator< for your type, or pass a comparison function to the algorithm."
        )
    if "no match for 'operator+'" in first and "int" in first and "std::string" in first:
        return (
            "std::accumulate is used with an initial value and element types that cannot be combined with operator+. "
            "The accumulator type and the element type must support the binary operation used by accumulate. "
            "Use an initial value of the same type as the elements, or use the four-argument form of accumulate with a custom op."
        )
    if "no match for 'operator-'" in first and "List_iterator" in first:
        return (
            "std::sort is used with iterators that do not support random access (e.g. std::list). "
            "std::sort requires random-access iterators. "
            "Use std::list::sort() for lists, or use a container that provides random-access iterators (e.g. std::vector)."
        )
    if "discards qualifiers" in first and "map" in first:
        return (
            "A const std::map is accessed with operator[] or a non-const method. "
            "operator[] can insert and is non-const; it cannot be used on a const map. "
            "Use find() or at() for read-only access to a const map."
        )
    if "assignment of read-only location" in first and "set" in first:
        return (
            "An attempt is made to modify an element of a set through an iterator. "
            "Set elements are const to preserve the ordering invariant. "
            "To change a value, remove the old element and insert the new one."
        )
    if "no matching member function for call to 'push_back'" in first:
        return (
            "An argument of the wrong type is passed to push_back. "
            "The argument type must match or be convertible to the container's element type. "
            "Pass a value of the correct type (e.g. int for vector<int>)."
        )
    if "iterator belongs to different container" in first:
        return (
            "An iterator from one container is used with a different container. "
            "Iterators are bound to the container that created them. "
            "Use an iterator from the same container (e.g. v1.erase(v1.begin()) not v1.erase(v2.begin()))."
        )
    if "conversion from 'int' to non-scalar type" in first and "iterator" in first:
        return (
            "An iterator is being initialized with an integer. "
            "Iterators are obtained from containers (e.g. v.begin()) or valid past-the-end values. "
            "Do not assign an integer to an iterator; use container.begin(), container.end(), or a valid iterator value."
        )

    # Linkage / definition
    if "undefined reference to" in first:
        return (
            "A symbol is declared (e.g. with extern) but no definition is found at link time. "
            "Every used symbol must have exactly one definition in the program (or in a linked library). "
            "Provide a definition in this translation unit or link the object file or library that defines it."
        )
    if "used but never defined" in first:
        return (
            "A function is declared but never defined in the program. "
            "The linker needs one definition for each used function. "
            "Add a definition for the function, or remove the call if it is not needed."
        )
    if "has both 'static' and 'extern' linkage" in first:
        return (
            "The same name is given both static and extern linkage. "
            "A name cannot be both file-local (static) and externally visible (extern) in the same declaration. "
            "Use either static or extern consistently for that name."
        )

    # Inline redefinition
    if "redefinition of 'void f()'" in first and "inline" in code:
        return (
            "The function f() is defined more than once in a way that violates inline rules. "
            "In C++, each function must have a single definition unless it is inline (with the same definition in every translation unit). "
            "Ensure the function is defined only once or properly declared inline in a header with identical definitions everywhere."
        )

    # Preprocessor (already partially covered)
    if "missing terminating '>' character" in first:
        return (
            "An #include directive is missing the closing angle bracket. "
            "Use #include <header> with both < and >. "
            "Add the closing '>' to the include line."
        )

    # Storage / static member / extern
    if "in-class initialization of non-const static" in first:
        return (
            "A non-const static data member is initialized inside the class definition. "
            "In C++ (before C++17), only const integral static members can be initialized in-class. "
            "Define and initialize the static member outside the class in one translation unit, or use inline (C++17)."
        )
    if "has both 'extern' and initializer" in first:
        return (
            "A variable is declared extern and given an initializer in the same declaration. "
            "extern declarations typically do not define; defining with an initializer should not use extern in that translation unit. "
            "Remove extern where you provide the definition and initializer, or remove the initializer from the extern declaration."
        )
    if "specifier not allowed here" in first and "thread_local" in first:
        return (
            "thread_local is used in a context where it is not allowed. "
            "thread_local can only be used for namespace-scope or block-scope variables. "
            "Move the declaration to an allowed scope or remove thread_local if not needed."
        )

    # Casts
    if "static_cast" in first and "casts away qualifiers" in first:
        return (
            "A static_cast attempts to remove const or other qualifiers from a pointer or reference. "
            "C++ does not allow casting away const with static_cast. "
            "Do not remove const; use a type that accepts const, or redesign if you need mutable access."
        )
    if "invalid static_cast" in first or "incompatible type" in first and "static_cast" in msg:
        return (
            "A static_cast is used between unrelated types (e.g. between two unrelated class pointers). "
            "static_cast allows safe conversions (e.g. numeric, up/down in hierarchy when well-defined). "
            "Use the correct cast (e.g. dynamic_cast for polymorphic types) or fix the type design."
        )
    if "reinterpret_cast" in first and "not allowed" in first:
        return (
            "A reinterpret_cast is used in a way the language does not allow. "
            "Not all type pairs can be reinterpret_cast; the standard restricts valid conversions. "
            "Use a different cast or representation that is allowed (e.g. through void* only where defined)."
        )
    if "dynamic_cast" in first and "not polymorphic" in first:
        return (
            "dynamic_cast is used on a pointer or reference to a non-polymorphic type. "
            "dynamic_cast requires the source type to have at least one virtual function. "
            "Make the base class polymorphic (add a virtual function) or use static_cast if the relationship is known."
        )
    if "typeid" in code and "lvalue required" in first:
        return (
            "The result of typeid is used on the left side of an assignment. "
            "typeid returns a std::type_info object that is not assignable. "
            "typeid is for querying type information only; do not assign to it."
        )

    # Enum
    if "cannot convert" in first and "Color" in first and "int" in first:
        return (
            "A scoped enum (enum class) value is used where an int is expected. "
            "Scoped enums do not implicitly convert to integers. "
            "Use an explicit cast (e.g. static_cast<int>(Color::Red)) when an integer is required."
        )
    if "no match for 'operator=='" in first and "Status" in first:
        return (
            "A scoped enum is compared directly to an integer. "
            "Scoped enums do not implicitly convert to int, so comparison with 0 or other integers fails. "
            "Compare with an enum value (e.g. Status::OK) or use static_cast<int>(...) for numeric comparison."
        )
    if "was not declared in this scope" in first and "did you mean" in first and "::" in first:
        return (
            "A scoped enum enumerator is used without its enum name. "
            "With enum class, enumerators must be qualified: EnumName::Enumerator. "
            "Use the full name (e.g. Traffic::Green) where you used Green."
        )

    # Namespace
    if "call of overloaded 'f()' is ambiguous" in first and "namespace" in code:
        return (
            "The name f() is found in more than one namespace brought in by using-directives, so the call is ambiguous. "
            "The compiler cannot choose which f() to call. "
            "Use a qualified name (e.g. A::f() or B::f()) or remove one of the using namespace directives."
        )
    if "reference to 'vector' is ambiguous" in first:
        return (
            "The name vector could refer to more than one type (e.g. std::vector and another vector in a different namespace). "
            "The compiler cannot resolve which one to use. "
            "Use the fully qualified name (e.g. std::vector<int>) or avoid using namespace in that scope."
        )
    if "has not been declared" in first and "Http" in first:
        return (
            "A nested namespace name is used without the full path. "
            "Nested namespaces must be qualified from the enclosing namespace or the global scope. "
            "Use the full path (e.g. Net::Http::Client) or a using directive for the nested namespace."
        )
    if "LongProjectName" in first and "has not been declared" in first:
        return (
            "A namespace alias refers to a namespace that has not been declared. "
            "The right-hand side of a namespace alias must be an existing namespace. "
            "Declare or include the namespace before using it in an alias."
        )
    if "redefinition of 'int {anonymous}::x'" in first:
        return (
            "The same name is defined in more than one anonymous namespace (e.g. in different translation units). "
            "Each anonymous namespace is distinct, but the same name in the same TU cannot be redefined. "
            "Use a single definition per TU or use different names or a named namespace."
        )

    # Exceptions
    if "inaccessible base of 'Derived'" in first:
        return (
            "A catch clause catches by reference to a base that is an inaccessible base of the thrown type. "
            "When catching by reference, the catch parameter type must be accessible. "
            "Catch by the derived type, or make the base an accessible base of the derived type (e.g. public inheritance)."
        )
    if "multiple handlers for type" in first:
        return (
            "Two or more catch blocks handle the same type. "
            "Each catch type in a try block must be distinct. "
            "Remove or merge the duplicate catch blocks."
        )
    if "catch parameter to be of abstract type" in first:
        return (
            "A catch clause declares its parameter as an abstract class type by value. "
            "Abstract types cannot be copied or instantiated. "
            "Catch by reference (e.g. catch (Abstract& e)) instead of by value."
        )
    if "dynamic exception specifications" in first or "ISO C++17 does not allow" in first:
        return (
            "A function is declared with a dynamic exception specification (e.g. throw(int)). "
            "Dynamic exception specifications are removed in C++17 and should not be used. "
            "Remove the throw(...) part from the function declaration; use noexcept where appropriate."
        )
    if "use of deleted function" in first and "NonCopyable" in first:
        return (
            "An object that is thrown must be copied or moved; the type has a deleted copy constructor. "
            "Throwing by value requires the type to be copyable or movable. "
            "Make the type copyable or movable, or throw a pointer or a type that can be copied."
        )
    if "throw' expression with no operand" in first:
        return (
            "A bare throw; is used outside a catch handler. "
            "throw; without an operand is only valid inside a catch block to rethrow the current exception. "
            "Use throw; only inside a catch block, or use throw expr; to throw a new exception."
        )
    if "expected '{' before ';' token" in first and "catch" in code:
        return (
            "A catch block has no body. "
            "After catch (type) there must be a compound statement in braces. "
            "Add a block in braces after the catch parameter, e.g. catch (...) { }."
        )
    if "expected primary-expression before 'catch'" in first:
        return (
            "A catch block appears without a preceding try block. "
            "Each catch must be immediately after a try block. "
            "Add a try block before the catch, or fix the syntax so try and catch are paired."
        )
    if "noexcept" in first and "terminate" in first:
        return (
            "An exception is thrown from a function declared noexcept. "
            "A noexcept function must not throw; if it does, std::terminate is called. "
            "Remove the throw, handle the error inside the function, or remove noexcept from the declaration."
        )

    # Overload / ambiguous
    if "call of overloaded" in first and "is ambiguous" in first:
        return (
            "More than one overloaded function matches the call, and neither is a better match. "
            "The compiler cannot choose between the candidates (e.g. int and double for a float argument). "
            "Add an explicit cast to the desired parameter type, or add or remove an overload to resolve the ambiguity."
        )

    # Deleted function
    if "use of deleted function" in first:
        if "= delete" in code:
            return (
                "A function or constructor that was explicitly deleted is being used. "
                "Deleted functions participate in overload resolution but may not be called. "
                "Use a different overload or API that is not deleted, or provide the missing operation if you control the type."
            )
        return (
            "A deleted function (e.g. copy constructor) is being invoked. "
            "The type disallows that operation by declaring it as = delete. "
            "Avoid calling the deleted operation; use a different constructor or method."
        )

    # Defaulted / operator
    if "cannot be defaulted" in first:
        return (
            "A special member is defaulted but the compiler cannot generate it (e.g. because a member has no default constructor). "
            "Defaulted members require that the compiler can generate the implementation. "
            "Provide an explicit definition, or ensure all members are default-constructible or otherwise compatible."
        )
    if "must have at least one class or enumeration type" in first and "operator" in first:
        return (
            "An operator is overloaded with only built-in types (e.g. int, int). "
            "User-defined operator overloads must have at least one parameter of class or enum type. "
            "Define the operator for a class or enum type, or use a named function instead."
        )
    if "must take exactly one argument" in first and "operator" in first:
        return (
            "A member operator is declared with the wrong number of parameters. "
            "Binary operators declared as members take one parameter (the right operand); unary operators take none. "
            "Fix the parameter list to match the operator (e.g. one parameter for operator,)."
        )
    if "must be a non-static member function" in first and "operator" in first:
        return (
            "An operator overload is declared static. "
            "Operator overloads that are members must be non-static. "
            "Remove the static specifier from the operator."
        )
    if "no return statement in function returning non-void" in first:
        return (
            "A function that returns a value (e.g. a reference or non-void type) has a path that does not return. "
            "Every path must return a value of the return type. "
            "Add a return statement on all paths, or change the return type to void if no value is returned."
        )

    # Attributes / consteval / static_assert
    if "unknown attribute" in first:
        return (
            "An attribute name is not recognized by the compiler. "
            "Attributes are compiler- or standard-specific. "
            "Fix the attribute name, remove it, or use a supported attribute for your compiler."
        )
    if "attribute" in first and "can only be applied" in first:
        return (
            "An attribute is used in a context where it is not allowed. "
            "Attributes like fallthrough apply only in specific places (e.g. before a null statement). "
            "Move or remove the attribute so it applies in an allowed context."
        )
    if "consteval" in first and "not a constant expression" in first:
        return (
            "A consteval function is called with a non-constant argument. "
            "consteval functions must be evaluated at compile time. "
            "Pass only constant expressions to the function, or change it to constexpr if runtime calls are needed."
        )
    if "variable length array" in first and "forbids" in first:
        return (
            "A variable-length array (VLA) is used. "
            "Standard C++ does not allow array sizes that are not constant expressions. "
            "Use a constant size or std::vector for a runtime-sized container."
        )
    if "static assertion failed" in first:
        return (
            "A static_assert condition evaluated to false. "
            "static_assert checks a compile-time condition and fails compilation if it is false. "
            "Fix the condition so it is true, or fix the types/values that make it false."
        )

    # Concepts / templates
    if "constraints not satisfied" in first or ("constraint" in first and "not satisfied" in msg):
        return (
            "A template or function call does not satisfy its required constraints (e.g. std::integral). "
            "Concepts restrict which types can be used with a template. "
            "Pass a type that satisfies the concept, or relax the constraint if the use is valid."
        )
    if "deduced conflicting types" in first or "Template Deduction" in first:
        return (
            "Template argument deduction produces conflicting types for the same parameter. "
            "Each template parameter must deduce to a single type across all arguments. "
            "Make the arguments agree in type, or specify the template arguments explicitly."
        )
    if "unexpanded parameter pack" in first:
        return (
            "A parameter pack is used in an expression without being expanded. "
            "Parameter packs must be expanded with ... in contexts that use each element. "
            "Expand the pack (e.g. with (args, ...) or a fold expression) where you use it."
        )

    # Lambda
    if "cannot be implicitly captured" in first and "lambda" in first:
        return (
            "A variable used inside a lambda is not captured. "
            "Lambdas must capture (by value or reference) or have a capture-default to use outer variables. "
            "Add the variable to the capture list, e.g. [x] or [=]."
        )
    if "assignment of read-only variable in lambda" in first:
        return (
            "A lambda tries to modify a variable captured by value. "
            "By default, captures by value are const inside the lambda. "
            "Mark the lambda mutable if you need to modify the copy: [x] () mutable { x = 1; }."
        )
    if "'this' was not captured" in first and "lambda" in first:
        return (
            "A member function or member is used inside a lambda without capturing this. "
            "To use the current object or its members, the lambda must capture this. "
            "Add this to the capture list: [this] or [=]."
        )
    if "invalid operands" in first and "operator+" in first and "lambda" in code:
        return (
            "A generic lambda is instantiated with argument types that do not support the operation used. "
            "The body uses an operation (e.g. +) that is not valid for the deduced types. "
            "Pass arguments of types that support the operation, or add a constraint."
        )
    if "no viable conversion from 'lambda'" in first and "std::function" in first:
        return (
            "A lambda cannot be converted to the expected std::function type. "
            "The lambda's parameters or return type do not match the target signature. "
            "Change the lambda signature to match the std::function, or use a different target type."
        )

    # Smart pointers
    if "dereferencing a released unique_ptr" in first:
        return (
            "A unique_ptr is dereferenced after release() has been called. "
            "After release(), the pointer is no longer managed and may be invalid. "
            "Do not dereference a unique_ptr after calling release(); use the returned raw pointer only if you assume ownership."
        )
    if "shift-count-overflow" in first or "left shift count" in first:
        return (
            "A shift count is too large or negative for the operand type. "
            "Shifting by a count greater than or equal to the bit width of the type is undefined behavior. "
            "Ensure the shift count is in range [0, width-1] for the operand type."
        )
    if "no match for 'operator|'" in first and "Mode" in first:
        return (
            "A bitwise operator is used on a scoped enum. "
            "Scoped enums do not support bitwise operations by default. "
            "Define operator| (and related operators) for the enum, or cast to the underlying type and back."
        )
    if "width of " in first and "exceeds its type" in first:
        return (
            "A bit-field is declared with a width larger than its type. "
            "The width in bits must not exceed the size of the underlying type. "
            "Use a larger type for the bit-field or reduce the width."
        )
    if "left shift of negative value" in first or "shift-negative" in first:
        return (
            "A negative value is used as the left operand of a left shift. "
            "Left-shifting a negative value has implementation-defined or undefined behavior. "
            "Use an unsigned type or a non-negative value for the left operand."
        )
    if "cannot take address of bit-field" in first:
        return (
            "The address-of operator is applied to a bit-field. "
            "Bit-fields may not have their address taken because they might not be byte-addressable. "
            "Use a copy in a variable and take the address of that variable if needed."
        )
    if "expected ';' before '~'" in first:
        return (
            "The bitwise NOT operator ~ is used with invalid syntax (e.g. space or typo). "
            "The correct form is ~expr. "
            "Remove any space or typo between the operand and ~."
        )
    if "enumerator value" in first and "not an integer constant" in first:
        return (
            "An enumeration constant is given a non-integer value. "
            "Enumerator values must be of integral type. "
            "Use an integer literal or constant expression for the enumerator value."
        )
    if "shift count is negative" in first:
        return (
            "The right operand of a shift is negative. "
            "Shift counts must be non-negative and less than the bit width. "
            "Use a non-negative shift count."
        )
    if "redefinition of 'Red'" in first and "enum" in code:
        return (
            "The same enumerator name appears in more than one unscoped enum in the same scope. "
            "Unscoped enums put enumerators in the surrounding scope, so names must be unique. "
            "Use enum class for separate scopes, or use different enumerator names."
        )
    if "invalid operands" in first and "operator>>=" in first and "bool" in first:
        return (
            "A bitwise compound assignment operator is applied to a bool. "
            "Such operators are not defined for bool in the way used. "
            "Use an integer type for bitwise operations, or use a different operation."
        )

    # Nodiscard / deprecated
    if "ignoring return value" in first and "nodiscard" in first:
        return (
            "The return value of a function declared [[nodiscard]] is discarded. "
            "The attribute indicates that ignoring the return value is likely a bug. "
            "Use the return value or assign it to (void) to explicitly ignore it if intended."
        )
    if "is deprecated" in first:
        return (
            "A deprecated function or entity is used. "
            "Deprecation warns that the feature may be removed in the future. "
            "Replace the use with the recommended alternative mentioned in the warning."
        )
    if "expression" in first and "constant expression" in first and "throw" in first:
        return (
            "A constexpr function or context evaluates a throw expression. "
            "Constant evaluation cannot throw. "
            "Ensure the constexpr path does not throw, or do not use the result in a constant expression."
        )
    if "unknown attribute" in first and "ignored" in first:
        return (
            "An attribute name is not recognized. "
            "Only known attributes have effect; others may be ignored. "
            "Fix the attribute name or remove it."
        )

    # Fallback: generic but no classification leakage
    return (
        "The code violates a rule of C++ that the compiler checks. "
        "Fix the construct indicated by the message: correct the syntax, types, or usage so it matches the language rules. "
        "Consult the compiler message for the exact location and adjust the code or add missing declarations or definitions."
    )


def refine_train_json(path: Path) -> None:
    """Load train.json, refine only explain_error targets, write back."""
    data = json.loads(path.read_text(encoding="utf-8"))
    for i, entry in enumerate(data):
        inp = entry.get("input", "")
        if not inp.startswith("explain_error:"):
            continue
        code, compiler_output = parse_explain_input(inp)
        entry["target"] = generate_explanation(code, compiler_output)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    explain_count = sum(1 for e in data if e.get("input", "").startswith("explain_error:"))
    print(f"Refined {explain_count} explain_error targets in {path}")


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    train_path = repo / "data" / "processed" / "train.json"
    refine_train_json(train_path)


if __name__ == "__main__":
    main()
