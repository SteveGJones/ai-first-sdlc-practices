# Deep Research Prompt: Mobile Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Mobile Architect. This agent will design mobile application
architectures, guide cross-platform vs native decisions, implement mobile
CI/CD, optimize mobile performance, and ensure mobile best practices.

## Research Areas

### 1. Mobile Architecture Patterns (2025-2026)
- What are current best practices for mobile app architecture (MVVM, MVI, Clean Architecture)?
- How do native iOS (SwiftUI) and Android (Jetpack Compose) architectures compare?
- What are the latest patterns for cross-platform development (React Native, Flutter, KMP)?
- How should mobile apps handle offline-first and sync patterns?
- What are current patterns for mobile modularization and feature architecture?

### 2. Cross-Platform Development
- How do React Native and Flutter compare in 2025-2026?
- What is the current state of Kotlin Multiplatform (KMP)?
- What are the latest patterns for sharing code between mobile and web?
- How should organizations decide between native and cross-platform?
- What are current patterns for platform-specific customization in cross-platform apps?

### 3. Mobile Performance & Optimization
- What are current best practices for mobile app performance?
- How should startup time, rendering, and memory be optimized?
- What are the latest patterns for mobile network optimization?
- How do mobile performance monitoring tools compare (Firebase, Datadog, New Relic)?
- What are current patterns for mobile app size optimization?

### 4. Mobile CI/CD & DevOps
- What are current best practices for mobile CI/CD pipelines?
- How should mobile build, test, and distribution be automated?
- What are the latest patterns for mobile code signing and provisioning?
- How do mobile CI platforms compare (Bitrise, Codemagic, Fastlane)?
- What are current patterns for mobile feature flags and A/B testing?

### 5. Mobile Security
- What are current best practices for mobile application security?
- How should mobile apps handle authentication and secure storage?
- What are the latest patterns for certificate pinning and network security?
- How do mobile security testing tools work (MobSF, OWASP MASTG)?
- What are current patterns for mobile app hardening and anti-tampering?

### 6. Mobile UX & Platform Guidelines
- What are current iOS Human Interface Guidelines best practices?
- How do Material Design 3 guidelines apply to Android development?
- What are the latest patterns for mobile accessibility?
- How should mobile apps handle different screen sizes and form factors?
- What are current patterns for mobile app navigation and state management?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Mobile architectures, cross-platform, performance, security the agent must know
2. **Decision Frameworks**: "When building [mobile app type], use [platform/pattern] because [reason]"
3. **Anti-Patterns Catalog**: Common mobile mistakes (ignoring platform guidelines, bloated bundles, no offline support)
4. **Tool & Technology Map**: Current mobile development tools with selection criteria
5. **Interaction Scripts**: How to respond to "choose mobile platform", "design mobile architecture", "optimize mobile performance"

## Agent Integration Points

This agent should:
- **Complement**: frontend-architect with mobile-specific expertise
- **Hand off to**: frontend-architect for web-specific architecture
- **Collaborate with**: api-architect on mobile API patterns (BFF, GraphQL)
- **Never overlap with**: frontend-architect on web frontend architecture
