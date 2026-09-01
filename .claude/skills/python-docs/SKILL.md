---
name: python-docs
description: Standardizes Python docstrings (Google style), generates ProperDocs markdown files, and builds Kroki diagrams. Use this whenever writing code comments, modifying architecture, or updating project documentation.
---

# Python Documentation Standards

You are the technical writer and documentation maintainer for this project. Follow these strict guidelines when generating or updating documentation.

## 1. Docstring Format (Google Style)
All Python functions, classes, and modules must use strict Google-style docstrings. Do not duplicate type hints in the docstring if they are already in the Python signature. Do NOT use Sphinx (reST) or NumPy formats.

**Example:**
```python
def fetch_metrics(service_id: str, retries: int = 3) -> dict:
    """Fetches operational metrics for a given service.

    Args:
        service_id: The unique identifier for the target service.
        retries: Number of connection attempts before failing.

    Returns:
        A dictionary containing the parsed metrics.

    Raises:
        ConnectionError: If the service is unreachable after retries.
    """

```

## 2. ProperDocs & Markdown Structure

All static site documentation lives in the `docs/` directory and is orchestrated via `properdocs.yml`.

* **Headings:** Use `#` for page titles (only once per file) and `##` for main sections.
* **Code Blocks:** Always specify the language (e.g., `bash`, `python`).
* **Linking:** Use relative paths to link between files inside `docs/`.

## 3. Diagrams (Kroki)

All architecture, sequence, and flow diagrams must be rendered using Kroki. Never generate raw image files (`.png`, `.svg`).

**Example (Mermaid via Kroki):**

```kroki-mermaid
sequenceDiagram
    participant User
    participant PyAgent
    User->>PyAgent: Trigger Action
    PyAgent-->>User: Return Result

```

## 4. Mandatory Triggers (The Enforcement Rule)

If you modify specific core systems, you MUST update their corresponding documentation before completing the task:

* **`MetricsService`**: If you add, modify, or remove a monitor, update `docs/metrics.md`.
* **`PyAgent`**: If you add or change an action, update `docs/actions.md`.

## 5. Verification & Linting

Before reporting that a documentation task is complete, you must run these checks:

1. Run `uv run ruff check --select D` to verify docstring compliance. Fix any errors.
2. Run `uv run properdocs build` to ensure there are no markdown or Kroki compilation errors.

## 6. Pre-Flight Checklist

When finishing a documentation or coding task covered by this skill, you MUST output this exact checklist to the user, verifying each step:

* [ ] Docstrings match Google style and passed Ruff checks.
* [ ] `docs/` files were updated (if `MetricsService` or `PyAgent` were changed).
* [ ] Kroki diagrams were used instead of raw image files.
* [ ] `uv run properdocs build` completed successfully.