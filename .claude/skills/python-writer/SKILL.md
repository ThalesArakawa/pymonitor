---
name: python-writer
description: Enforces strict SOLID principles, Clean Code practices, and strict type hinting when writing or refactoring Python code. Use this for all feature development.
---

# Python Clean Code & SOLID Standards

You are a senior Python engineer. Your primary goal is to write maintainable, decoupled, and readable code. You must adhere to the following principles without exception.

## 1. Clean Code Baseline
*   **Naming:** Variable and function names must be explicit and unabbreviated (e.g., `calculate_annual_revenue` not `calc_rev`).
*   **Function Size:** Functions must do exactly one thing. If a function exceeds 20 lines or requires multiple levels of indentation, extract helper functions.
*   **Arguments:** Keep function arguments to a maximum of 3. If you need more, group them into a `@dataclass` or `TypedDict`.
*   **Error Handling:** Fail fast. Raise specific, custom exceptions (e.g., `raise InvalidMonitorConfigError(...)`). NEVER use bare `except:` or `except Exception:`.

## 2. SOLID Implementation in Python
*   **Single Responsibility (SRP):** Classes should have only one reason to change. Separate data retrieval, business logic, and presentation.
*   **Open/Closed (OCP):** Software entities should be open for extension, but closed for modification. Use Python's `typing.Protocol` or `abc.ABC` to define interfaces that can be implemented by new classes without touching existing core logic.
*   **Liskov Substitution (LSP):** Subclasses must be substitutable for their base classes. Do not override a method to do something fundamentally different or raise unexpected exceptions.
*   **Interface Segregation (ISP):** Clients should not be forced to depend on interfaces they do not use. Prefer multiple small `Protocol` definitions over one massive base class.
*   **Dependency Inversion (DIP):** High-level modules must not depend on low-level modules; both should depend on abstractions. Inject dependencies via `__init__` rather than hardcoding instantiations inside methods.

## 3. Strict Typing
Every function, method, and variable must have strict type hints. 
*   **Good:** `def process_data(client: MetricsClient, retries: int = 3) -> None:`
*   **Bad:** `def process_data(client, retries=3):`

## 4. Example: Dependency Inversion & OCP
**Bad (Tightly Coupled):**
```python
class PyAgent:
    def __init__(self):
        self.logger = FileLogger() # Hardcoded dependency
        
    def execute(self):
        self.logger.log("Executing...")

```

**Good (Decoupled via Protocol):**

```python
from typing import Protocol

class Logger(Protocol):
    def log(self, message: str) -> None: ...

class PyAgent:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger # Injected dependency
        
    def execute(self) -> None:
        self.logger.log("Executing...")

```

## 5. Verification & Linting

Before reporting a coding task as complete, you must:

1. Run `uv run ruff check` to ensure syntax and import cleanliness.
2. Run `uv run ruff format` to enforce formatting.
3. Run `uv run mypy .` (if installed) to verify strict type correctness.

## 6. Pre-Flight Checklist

When finishing a feature, you MUST output this exact checklist:

* [ ] Functions do one thing and have < 4 arguments.
* [ ] Dependencies are injected via `__init__` or function arguments (DIP).
* [ ] New features extend functionality without modifying core classes (OCP).
* [ ] All functions have strict type hints and passed `uv run ruff check`.