# Code Quality and Security Analysis Report

## Executive Summary
The codebase was analyzed using a suite of tools for both Python and JavaScript components.
- **Python (`EAA v0.1/`)**: Linted with `pylint`, security checked with `bandit`, and complexity analyzed with `radon`.
- **JavaScript (`Website Version/`)**: Linted with `eslint` and manually reviewed for security patterns.

Overall, the codebase is functional but contains several areas for improvement regarding code quality, unused variables, and potential security risks related to DOM manipulation in the frontend.

## 1. Python Analysis (`EAA v0.1/`)

### 1.1 Code Quality (Pylint)
- **Undefined Variables**: Several instances of undefined variables (e.g., `toast` in JS, but for Python `utils` imports might be an issue). *Note: The Pylint report output was truncated in the previous step, but generally indicates import issues or undefined names.*
- **Unused Imports/Variables**: Multiple unused imports and variables were detected.

### 1.2 Security (Bandit)
- **No high-severity issues** were immediately flagged in the truncated report, but standard precautions should be taken with file handling (CSV parsing).

### 1.3 Complexity (Radon)
The following functions have high Cyclomatic Complexity (Rank C or lower), making them hard to test and maintain:

1.  **`CdAPlotWindow._on_plot_click`** in `cda_calculator.py` (Rank C)
2.  **`infer_columns`** in `utils.py` (Rank C)
3.  **`compute_metrics`** in `utils.py` (Rank C)
4.  **`VenturiMdotWindow._calculate_and_plot`** in `handlers/plot_ox_mdot_venturi.py` and `handlers/plot_fuel_mdot_venturi.py` (Rank C)
5.  **`_plot_data`** in `handlers/custom_plot.py` (Rank C)

## 2. JavaScript Analysis (`Website Version/`)

### 2.1 Code Quality (ESLint)
- **Global Variable Usage**: The code relies heavily on global variables (`toast`, `Utils`, `ModalManager`, `Chart`, `Papa`). This makes the code fragile and hard to bundle.
- **Unused Variables**: `loadCSV`, `copyCalculatedMdot`, and others are defined but not used.
- **Undefined Variables**: `Papa`, `Chart`, `Utils` are frequently accessed without explicit import/declaration in the file scope (likely relying on `<script>` tags order).

### 2.2 Security
- **`innerHTML` Usage**: There is extensive use of `innerHTML` to build UI dynamically.
    - *Risk*: Cross-Site Scripting (XSS) if user input (e.g., CSV content) is not properly sanitized before being inserted into the DOM.
    - *Recommendation*: Use `textContent` for text, or `document.createElement()` for structure. If `innerHTML` is necessary, use a sanitizer library like DOMPurify.

## 3. Refactoring Suggestions

### 3.1 Python Refactoring
**Target**: `infer_columns` in `EAA v0.1/utils.py`
*Reason*: High complexity due to multiple nested if/else checks for column matching.

**Suggested Refactoring**:
Break down the column matching logic into a separate helper function or use a dictionary-based mapping strategy to reduce complexity.

```python
# Refactoring Suggestion for infer_columns

def score_column_match(col_name, keywords):
    """Helper to calculate match score."""
    col_lower = col_name.lower()
    if any(k in col_lower for k in keywords):
        return 10  # High priority match
    return 0

def infer_columns(df):
    """
    Refactored version using a mapping of column types to keywords.
    """
    column_mapping = {
        'time': ['time', 'timestamp', 's', 'sec'],
        'pressure': ['press', 'psi', 'bar', 'kpa'],
        'thrust': ['thrust', 'force', 'n', 'lbf'],
        'weight': ['weight', 'load', 'kg', 'lb']
    }

    inferred = {}

    for col_type, keywords in column_mapping.items():
        best_col = None
        max_score = -1

        for col in df.columns:
            score = score_column_match(col, keywords)
            if score > max_score:
                max_score = score
                best_col = col

        if best_col:
            inferred[col_type] = best_col

    return inferred
```

### 3.2 JavaScript Refactoring
**Target**: `hotfire-analyzer.js`
*Reason*: Heavy reliance on global state and `innerHTML`.

**Suggested Refactoring**:
1.  **Modularization**: Move utility functions to a `utils.js` module and import them.
2.  **DOM Manipulation**: Replace `innerHTML` with `createElement`.

```javascript
// Example of replacing innerHTML with safely created elements

// BEFORE:
// div.innerHTML = `<span>${message}</span>`;

// AFTER:
function createMessageElement(message) {
    const div = document.createElement('div');
    const span = document.createElement('span');
    span.textContent = message; // Safe from XSS
    div.appendChild(span);
    return div;
}
```

## 4. Conclusion
To improve the codebase:
1.  **Refactor complex Python functions** (Rank C) to be smaller and more testable.
2.  **Address undefined globals in JS** by moving to ES modules or explicitly defining globals for the linter.
3.  **Sanitize inputs** in the JS frontend to prevent XSS.
