# Deep Research Prompt: UX/UI Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a UX/UI Architect. This agent will design user experiences,
create design systems, implement accessibility standards, conduct design
reviews, plan user research, and ensure interfaces are intuitive, inclusive,
and effective for projects of all sizes.

The resulting agent should be able to create information architectures,
design component systems, evaluate usability, implement WCAG accessibility
standards, and guide design-development handoff when engaged by the
development team.

## Context

This agent is needed because user experience design has evolved significantly
with design systems, accessibility-first approaches, AI-powered interfaces,
and new interaction paradigms. The existing agent has good fundamental UX/UI
knowledge but needs depth on modern design systems at scale, accessibility
compliance automation, AI/conversational UI patterns, and design token
architecture. The frontend-architect handles implementation; this agent
owns the design and user experience strategy.

## Research Areas

### 1. Modern Design Systems (2025-2026)
- What are current best practices for building and maintaining design systems?
- How have design token architectures evolved (Style Dictionary, Figma variables)?
- What are the latest patterns for multi-brand and multi-platform design systems?
- How do design systems integrate with development frameworks (React, Vue, Web Components)?
- What tools support design system management and documentation (Storybook, Zeroheight)?

### 2. Accessibility & Inclusive Design
- What are the current WCAG 2.2 and upcoming WCAG 3.0 requirements?
- How should organizations implement accessibility testing automation?
- What are the latest patterns for inclusive design beyond compliance?
- How do assistive technologies interact with modern web applications?
- What tools support accessibility testing (axe, Lighthouse, WAVE)?

### 3. User Research & Testing Methods
- What are current best practices for user research in 2025-2026?
- How have remote and unmoderated user testing platforms evolved?
- What are the latest patterns for quantitative UX metrics (SUS, CSAT, task completion)?
- How should organizations implement continuous discovery and research ops?
- What are current practices for A/B testing and experimentation in UX?

### 4. Information Architecture & Navigation
- What are current best practices for information architecture?
- How should complex applications handle navigation patterns?
- What are the latest patterns for search UX and content findability?
- How do card sorting and tree testing techniques inform IA decisions?
- What are current patterns for progressive disclosure and content hierarchy?

### 5. Interaction Design & Motion
- What are current best practices for micro-interactions and animation?
- How should designers approach responsive and adaptive design?
- What are the latest patterns for gesture-based and voice interfaces?
- How do animation libraries and tools support interaction design (Framer Motion, Lottie)?
- What are current patterns for loading states, transitions, and feedback?

### 6. AI-Powered UX Patterns (Emerging)
- How are AI interfaces changing UX design patterns?
- What are current best practices for conversational UI and chatbot design?
- How should organizations design AI-human collaboration interfaces?
- What are the latest patterns for generative AI interfaces (prompts, results display)?
- How do AI recommendations and personalization affect UX?

### 7. Design-Development Collaboration
- What are current best practices for design-to-code handoff?
- How have tools like Figma Dev Mode changed the handoff process?
- What are the latest patterns for design tokens and style API integration?
- How should design reviews and critique processes work?
- What are current practices for design QA and visual regression testing?

### 8. Data Visualization & Dashboard Design
- What are current best practices for data visualization design?
- How should complex dashboards be designed for different user roles?
- What are the latest patterns for real-time data display and updates?
- What visualization libraries support design system integration (D3, ECharts, Recharts)?
- How should organizations approach mobile-responsive data visualization?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Design system architecture, accessibility standards, user research methods, interaction patterns the agent must know
2. **Decision Frameworks**: "When designing [interface type] for [user group], use [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common UX mistakes (mystery meat navigation, modal overuse, accessibility theater, dark patterns, inconsistent design)
4. **Tool & Technology Map**: Current design tools (Figma, design systems, accessibility testing, user research) with selection criteria
5. **Interaction Scripts**: How to respond to "review our UX design", "build a design system", "make our app accessible", "design a dashboard"

## Agent Integration Points

This agent should:
- **Complement**: frontend-architect by owning design strategy (frontend-architect handles implementation, UX/UI architect handles design decisions)
- **Hand off to**: frontend-architect for technical implementation of designs
- **Receive from**: solution-architect for user requirements and business constraints
- **Collaborate with**: documentation-architect on content strategy and writing
- **Never overlap with**: frontend-architect on framework selection, build tooling, or code architecture
