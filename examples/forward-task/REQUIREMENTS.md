# Fixture review task

Review `ratio.py` against this contract. This is synthetic input for a fresh reviewer, not production software.

- Accept a non-empty sequence of non-negative real readings.
- Return readings divided by the maximum.
- An all-zero sequence must return zeros of the same length.
- An empty sequence or any negative reading must raise ValueError.
- Keep the function signature. There is no network, deployment or customer data.
