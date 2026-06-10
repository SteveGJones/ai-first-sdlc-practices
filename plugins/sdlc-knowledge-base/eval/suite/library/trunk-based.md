---
layer: development
confidence: medium
---
# Trunk-Based Development

Trunk-based development is a branching model where developers collaborate on a single branch called trunk. Developers commit small changes to trunk at least once a day to avoid long-lived divergent branches.

Short-lived feature branches are permitted but should live for no more than a couple of days before being merged. Long-lived branches are discouraged because they cause painful merge conflicts and delay integration.

Trunk-based development pairs well with feature flags, which let teams merge incomplete work to trunk while keeping it hidden from users until it is ready.
