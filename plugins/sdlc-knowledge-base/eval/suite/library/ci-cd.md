---
layer: development
confidence: high
---
# Continuous Integration and Continuous Delivery

Continuous integration is the practice of merging all developer working copies to a shared mainline several times a day. Each integration is verified by an automated build and an automated test suite to detect integration errors as quickly as possible.

Continuous delivery extends continuous integration by ensuring that the software can be released to production at any time. Every change that passes the automated tests is a release candidate. A deployment pipeline automates the steps of building, testing, and deploying the application.

A core principle of continuous delivery is to keep the mainline always in a deployable state. Failing builds should be fixed immediately, and the team should stop the line until the build is green again.
