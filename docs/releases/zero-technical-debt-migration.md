# Migration Guide: Zero Technical Debt Policy

**Version:** 1.5.0
**Release Date:** 2024-07-25
**Impact:** BREAKING CHANGES - Requires architectural documentation before coding

---

## 🚨 Critical Changes for AI Agents

This release introduces **mandatory Architecture-First Development**. AI agents MUST complete ALL architectural documentation before writing ANY code. This is a breaking change that affects your workflow.

---

## 📋 Migration Checklist

### For AI Agents Currently Using the Framework

1. **Update Your CLAUDE.md**
   ```bash
   # Backup current CLAUDE.md
   cp CLAUDE.md CLAUDE.md.backup

   # Download the new mandatory section
   curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/CLAUDE.md | grep -A 200 "MANDATORY: Architecture-First Development" > architecture-section.md

   # Manually add the new section to your CLAUDE.md after the Zero Technical Debt Policy section
   ```

2. **Create Architecture Directory Structure**
   ```bash
   # Create required directories
   mkdir -p docs/architecture/decisions

   # Download all architecture templates
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/requirements-traceability-matrix.md
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/what-if-analysis.md
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/architecture-decision-record.md
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/system-invariants.md
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/integration-design.md
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/templates/architecture/failure-mode-analysis.md

   # Move templates to correct location
   mv *.md templates/architecture/
   ```

3. **Download New Validation Tools**
   ```bash
   # Architecture validator (REQUIRED)
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/tools/validation/validate-architecture.py
   chmod +x validate-architecture.py
   mv validate-architecture.py tools/validation/

   # Technical debt detector
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/tools/validation/check-technical-debt.py
   chmod +x check-technical-debt.py
   mv check-technical-debt.py tools/validation/

   # Updated validation pipeline
   curl -LO https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/tools/validation/validate-pipeline.py
   chmod +x validate-pipeline.py
   mv validate-pipeline.py tools/validation/
   ```

4. **Update Your Workflow**

   **OLD WORKFLOW:**
   ```
   Feature Proposal → Implementation → Retrospective → PR
   ```

   **NEW WORKFLOW (MANDATORY):**
   ```
   Feature Proposal → Architecture Docs (ALL 6) → Implementation → Retrospective → PR
   ```

5. **For Work in Progress**

   If you have features currently being implemented:

   a. **STOP all coding immediately**

   b. **Create architecture documents for current feature**:
   ```bash
   # Copy templates to docs/architecture/
   cp templates/architecture/*.md docs/architecture/

   # Fill out EVERY document completely
   # This is NOT optional
   ```

   c. **Validate architecture**:
   ```bash
   python tools/validation/validate-architecture.py
   # MUST pass before continuing
   ```

   d. **Only then resume coding**

6. **Update CI/CD Pipeline**

   Add architecture validation to your CI/CD:

   ```yaml
   # GitHub Actions example
   - name: Validate Architecture
     run: |
       python tools/validation/validate-architecture.py --strict
       if [ $? -ne 0 ]; then
         echo "❌ Architecture validation failed"
         echo "Complete ALL architecture documents before coding"
         exit 1
       fi
   ```

---

## 🔄 What's Changed

### New Mandatory Requirements

1. **Six Architecture Documents** (BEFORE ANY CODE):
   - Requirements Traceability Matrix
   - What-If Analysis
   - Architecture Decision Records
   - System Invariants
   - Integration Design
   - Failure Mode Analysis

2. **New Validation Checks**:
   - `architecture` - Validates all 6 docs exist and are complete
   - `technical-debt` - Scans for ANY debt indicators
   - `type-safety` - Ensures strict typing in all languages

3. **Zero Tolerance Policy**:
   - NO `any` types
   - NO TODO/FIXME comments
   - NO commented-out code
   - NO error suppression
   - NO outdated dependencies

### Updated Tools

- **validate-pipeline.py**: Now includes architecture, technical-debt, and type-safety checks
- **validate-architecture.py**: NEW - Enforces architecture-first development
- **check-technical-debt.py**: NEW - Standalone debt detection with detailed reporting

---

## 💡 For Human Developers

While this policy is designed for AI agents who have no excuses for technical debt, human developers should:

1. Use the architecture templates as guides
2. Fill them out to the best of your ability
3. Focus on the most critical aspects for your feature
4. Iterate and improve over time

The goal is to think architecturally BEFORE coding, preventing costly rewrites.

---

## 🚨 Breaking Changes

1. **Validation Pipeline**: Will now FAIL if architecture documents are missing
2. **PR Checks**: Will block merge without complete architecture
3. **Setup Script**: Will create architecture directories by default

---

## 📚 Example Migration

Here's a complete example for an AI agent migrating an existing project:

```bash
# 1. Check current version
cat VERSION
# If < 1.5.0, proceed with migration

# 2. Create full backup
git add -A
git commit -m "chore: backup before Zero Technical Debt migration"

# 3. Run migration commands
mkdir -p docs/architecture/decisions
mkdir -p templates/architecture
mkdir -p tools/validation

# 4. Download all required files
# (Run all curl commands from sections above)

# 5. Update CLAUDE.md with new architecture section
# (Manual step - add the architecture-first section)

# 6. For current feature branch
git stash  # Stash any uncommitted work

# Create architecture docs
cp templates/architecture/*.md docs/architecture/
# Fill out all 6 documents completely

# Validate
python tools/validation/validate-architecture.py

# Only after validation passes
git stash pop  # Resume work

# 7. Update VERSION file
echo "1.5.0" > VERSION

# 8. Commit migration
git add -A
git commit -m "feat: migrate to Zero Technical Debt policy v1.5.0

- Added mandatory architecture-first development
- Created all 6 architecture document templates
- Updated validation pipeline with new checks
- Ready for zero technical debt compliance"
```

---

## ❓ FAQ

**Q: What if I'm in the middle of coding a feature?**
A: Stop immediately, create all 6 architecture documents, validate them, then resume.

**Q: Can I skip some architecture documents for simple features?**
A: NO. All 6 are mandatory. This is zero-tolerance.

**Q: What if the architecture changes during implementation?**
A: Update the architecture documents FIRST, then update the code.

**Q: How detailed must the architecture documents be?**
A: Complete enough that someone could implement the feature without asking questions.

**Q: Can I use placeholders or templates?**
A: NO. The validator checks for actual content, not templates.

---

## 🆘 Getting Help

If you encounter issues during migration:

1. Run validation with verbose output:
   ```bash
   python tools/validation/validate-architecture.py --export markdown
   ```

2. Check for technical debt:
   ```bash
   python tools/validation/check-technical-debt.py --format markdown
   ```

3. Review the Zero Technical Debt policy:
   ```bash
   cat ZERO-TECHNICAL-DEBT.md
   ```

---

## ✅ Migration Complete Checklist

- [ ] CLAUDE.md updated with Architecture-First section
- [ ] Architecture directory structure created
- [ ] All 6 architecture templates downloaded
- [ ] Validation tools downloaded and executable
- [ ] Current work has architecture documents
- [ ] Architecture validation passes
- [ ] CI/CD updated with architecture checks
- [ ] VERSION file shows 1.5.0
- [ ] All team members notified of new requirements

---

**Remember**: This is about building quality in from the start, not adding it later. Think like an architect, code like a craftsman.