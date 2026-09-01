---
name: python-docs
description: Standardizes Python docstrings (Google style), generates ProperDocs markdown files, and builds Kroki diagrams. Use this whenever writing code comments, modifying architecture, or updating project documentation.
---

# Python Documentation Standards

You are the technical writer and documentation maintainer for this project. Follow these strict guidelines when generating or updating documentation.

## 1. Docstring Format (Google Style)
All Python functions, classes, and modules must use strict Google-style docstrings.
*   **Format:** Use `"""` for all docstrings.
*   **Sections:** Use explicit `Args:`, `Returns:`, `Raises:`, and `Yields:` sections where applicable.
*   **Types:** Do not duplicate type hints in the docstring if they are already in the Python function signature.
*   **Anti-pattern:** Do NOT use Sphinx (reST) or NumPy formats.

## 2. ProperDocs & Markdown Structure
All static site documentation lives in the `docs/` directory and is orchestrated via `properdocs.yml`.
*   **Headings:** Use `#` for page titles and `##` for main sections. Never use `#` more than once per file.
*   **Code Blocks:** Always specify the language (e.g., ` ```python ` or ` ```bash `).
*   **Linking:** Use relative paths to link between markdown files in the `docs/` directory.

## 3. Diagrams (Kroki)
All architecture, sequence, and flow diagrams must be rendered using Kroki.
*   **Syntax:** Write the diagram definition inside a Kroki-supported code block (e.g., ` ```kroki-plantuml ` or ` ```kroki-mermaid ` depending on the plugin configuration).
*   **Context:** Never generate raw image files (`.png`, `.svg`) for diagrams. Always embed the text-based generation code directly into the markdown.
*   **Complexity:** Keep diagrams focused. If a system has more than 6 interacting components, break it into two separate diagrams.

## 4. Mandatory Triggers (The Enforcement Rule)
If you modify specific core systems, you MUST update their corresponding documentation before completing the task:
*   **MetricsService:** If you add, modify, or remove a monitor, update the `docs/metrics.md` (or equivalent) file.
*   **PyAgent:** If you add or change an action, update the `docs/actions.md` (or equivalent) file.

## 5. Verification
Before reporting that a documentation task is complete, you must verify it builds correctly:
1. Run `uv run properdocs build` to ensure there are no compilation errors.
2. If the build fails, fix the markdown or Kroki syntax and rebuild.