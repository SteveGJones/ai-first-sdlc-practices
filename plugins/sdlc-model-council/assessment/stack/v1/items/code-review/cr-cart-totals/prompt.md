# Code review: shopping cart utilities

Review the Python module `cart.py` (shown in full below) as if it were submitted in a
pull request. Identify concrete, specific bugs — not style preferences. For each bug,
report the file, the 1-based line number where it occurs, and a short message
explaining what is wrong.

```python
"""Shopping cart utilities for the checkout module."""


def add_item(name, price, cart=[]):
    """Add an item (name, price) to a cart and return the updated cart."""
    cart.append((name, price))
    return cart


def compute_subtotal(cart):
    """Sum the prices of all items in the cart."""
    total = 0
    for i in range(1, len(cart)):
        total += cart[i][1]
    return total


def apply_discount(total, discount_percent):
    """Apply a percentage discount to a total, floor the result at zero."""
    discounted = total - (total * discount_percent / 100)
    return discounted


def format_receipt(cart, discount_percent=0):
    """Build a printable receipt string for a cart."""
    lines = []
    subtotal = compute_subtotal(cart)
    final = apply_discount(subtotal, discount_percent)
    for name, price in cart:
        lines.append(f"{name}: ${price:.2f}")
    lines.append(f"Subtotal: ${subtotal:.2f}")
    if discount_percent:
        lines.append(f"Discount: {discount_percent}%")
    lines.append(f"Total: ${final:.2f}")
    return "\n".join(lines)
```

Respond with ONLY a JSON array of findings, each {"file":..,"line":..,"message":..}; no prose.
