---
layer: methodology
confidence: high
---
# Software Testing

The test pyramid recommends many fast unit tests, fewer integration tests, and a small number of slow end-to-end tests. Unit tests form the broad base of the pyramid because they are cheap to write and fast to run.

In test-driven development the failing test is written before the implementation code. The cycle is red, green, refactor: write a failing test, write the minimal code to make it pass, then refactor while keeping the tests green.

Code coverage measures the percentage of lines exercised by the test suite. Coverage is a useful signal but high coverage alone does not guarantee that the tests are meaningful.
