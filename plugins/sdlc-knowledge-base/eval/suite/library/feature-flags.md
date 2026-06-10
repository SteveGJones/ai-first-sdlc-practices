---
layer: development
confidence: medium
---
# Feature Flags

A feature flag is a configuration switch that lets a team turn a feature on or off at runtime without deploying new code. Feature flags decouple deployment of code from release of functionality.

Feature flags enable progressive delivery techniques such as canary releases and percentage-based rollouts. A team can expose a new feature to one percent of users first and increase the percentage as confidence grows.

Stale feature flags accumulate as technical debt and should be removed once a feature is fully rolled out. Long-lived flags increase the number of code paths the team must test and maintain.
