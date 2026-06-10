---
layer: development
confidence: medium
---
# Deployment Strategies

A blue-green deployment runs two identical production environments called blue and green. Traffic is switched from the old environment to the new one all at once, and the old environment is kept ready for an instant rollback.

A canary deployment releases the new version to a small subset of users before rolling it out to everyone. If the canary shows elevated errors the team rolls back before most users are affected.

A rolling deployment gradually replaces instances of the old version with the new version a few at a time. Rolling deployments avoid downtime but make rollback slower than a blue-green switch.
