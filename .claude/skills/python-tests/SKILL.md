---
name: python-tests
description: Writes robust, deterministic unit tests using Pytest. Enforces the Arrange-Act-Assert pattern, strict mocking boundaries, and coverage verification. Use this whenever writing or modifying tests.
---

# Python Unit Testing Standards

You are a QA automation engineer. Your goal is to write deterministic, fast, and isolated unit tests. 

## 1. Framework & Naming
*   **Engine:** Use `pytest` exclusively. Do not use the standard library `unittest.TestCase` classes.
*   **Naming Convention:** Test files must be named `test_<module>.py`. Test functions must follow the pattern `test_<method>_<condition>_<expected_behavior>` (e.g., `test_fetch_metrics_with_invalid_id_raises_error`). Use classes only for grouping related tests; do not use them for setup/teardown.
*   **Fixtures:** Use `pytest` fixtures for setup and teardown. Avoid `setUp` and `tearDown` methods. Think about which fixtures can be reused across multiple tests. Add them to `tests/conftest.py` for global scope, if can be reused over all tests. If a fixture is only used in one test file, define it in that file. If a fixture is only used by unit tests for a specific module, define it in a `tests/unit/conftest.py` file. If a fixture is only used by integration tests for a specific module, define it in a `tests/integration/conftest.py` file.
*   **Folder Structure:** Place all unit tests files in a `tests/unit/` directory at the root of the project. Mirror the source code structure for clarity. Place all integration tests in a `tests/integration/` directory.

## 2. Structure (Arrange, Act, Assert)
Every test must be visibly separated into three distinct blocks using blank lines.
*   **Arrange:** Set up the data, mocks, and instantiations.
*   **Act:** Execute the single function or method being tested.
*   **Assert:** Verify the results or side effects.

**Example:**
```python
def test_calculate_discount_with_valid_code_applies_reduction():
    # Arrange
    cart = Cart(total=100.0)
    coupon = MockCoupon(code="SAVE20", discount=0.20)

    # Act
    result = calculate_discount(cart, coupon)

    # Assert
    assert result == 80.0
```

## 3. Mocking & Isolation

* **Boundary Control:** Only mock external dependencies, network calls (I/O), databases, or time (`datetime.now()`). NEVER mock the internal logic of the System Under Test (SUT).
* **Tools:** Prefer `pytest` fixtures for reusable setup. Use `unittest.mock.MagicMock` or `pytest-mock` (mocker) for isolating dependencies.

## 4. Testing SOLID Code

Because the application uses Dependency Inversion (from our Python writer standards), you must inject mock dependencies directly into constructors during testing rather than relying on `mock.patch` where possible.

## 5. Verification

Before reporting that a test task is complete, you must verify the test passes and does not break existing suites.

1. Run `uv run pytest path/to/test_file.py` to ensure the new test passes.
2. Run `uv run pytest` on the whole suite to ensure no regressions.

## 6. Pre-Flight Checklist

When finishing a testing task, you MUST output this exact checklist:

* [ ] Tests follow the explicit Arrange-Act-Assert structure.
* [ ] Only external boundaries/I/O are mocked; core logic is tested directly.
* [ ] Dependencies are injected cleanly using fixtures or direct instantiation.
* [ ] `uv run pytest` executed successfully and all tests pass.