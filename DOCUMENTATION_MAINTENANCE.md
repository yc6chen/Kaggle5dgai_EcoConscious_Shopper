# Documentation Maintenance Guide

> Guidelines for maintaining, organizing, and consolidating project documentation

## Table of Contents

1. [Documentation Structure](#documentation-structure)
2. [Documentation Standards](#documentation-standards)
3. [Maintenance Schedule](#maintenance-schedule)
4. [Consolidation Guidelines](#consolidation-guidelines)
5. [Version Control](#version-control)
6. [Documentation Templates](#documentation-templates)

---

## Documentation Structure

### Current Documentation Files

```
Kaggle5dgai_EcoConscious_Shopper/
├── README.md                      # Primary documentation (KEEP)
├── DEPLOYMENT_GUIDE.md            # Build/deploy instructions (KEEP)
├── DOCUMENTATION_MAINTENANCE.md   # This file (KEEP)
├── Knowledge_Base/                # Reference materials (EXCLUDED from git)
│   └── *.md                       # Training/course materials
└── Prompt.md                      # Project specification (EXCLUDED from git)
```

### Documentation Hierarchy

**Tier 1 - Essential (Always Keep)**
- `README.md` - Project overview, quick start, architecture
- `DEPLOYMENT_GUIDE.md` - Build, run, deploy instructions

**Tier 2 - Reference (Keep Updated)**
- `DOCUMENTATION_MAINTENANCE.md` - This guide
- `CONTRIBUTING.md` - Contribution guidelines (create if project becomes open)
- `CHANGELOG.md` - Version history (create when versioning starts)

**Tier 3 - Knowledge Base (Excluded from Repository)**
- `Knowledge_Base/*.md` - Course materials and training notes
- `Prompt.md` - Original project specification
- Internal notes and brainstorming docs

**Tier 4 - Auto-Generated (Can Be Regenerated)**
- API documentation (from FastAPI/Swagger)
- Code documentation (from docstrings)
- Test coverage reports

---

## Documentation Standards

### File Naming Conventions

**DO:**
- Use UPPERCASE for important guides: `README.md`, `DEPLOYMENT_GUIDE.md`
- Use descriptive names: `API_REFERENCE.md` not `api.md`
- Use underscores for multi-word files: `DOCUMENTATION_MAINTENANCE.md`

**DON'T:**
- Create redundant files: `readme.txt`, `README.txt`, `README.markdown`
- Use generic names: `doc.md`, `notes.md`, `temp.md`
- Keep outdated files: `README_OLD.md`, `DEPLOYMENT_v1.md`

### Document Structure Standard

Every documentation file should follow this structure:

```markdown
# Title

> Brief one-line description

## Table of Contents
(if document is >3 sections)

## Section 1

### Subsection 1.1

Content...

---

## Support / References / Contact
(at the end)

---

**Last Updated:** YYYY-MM-DD
```

### Writing Style Guidelines

1. **Be Concise**
   - ✅ "Install dependencies with `pip install -r requirements.txt`"
   - ❌ "You should now proceed to install all of the Python package dependencies that are listed in the requirements.txt file by running pip install with the -r flag"

2. **Use Active Voice**
   - ✅ "Deploy the application to Vertex AI"
   - ❌ "The application should be deployed to Vertex AI"

3. **Provide Examples**
   - Always include code examples
   - Show expected output
   - Include error scenarios

4. **Use Consistent Formatting**
   - Code blocks: ` ```bash ` for shell commands
   - Inline code: `` `variable_name` ``
   - Emphasis: **bold** for important, *italic* for definitions

---

## Maintenance Schedule

### Weekly Tasks

- [ ] Review open issues for documentation requests
- [ ] Check for broken links in README.md
- [ ] Update "Last Updated" timestamps on changed files

### Monthly Tasks

- [ ] Review all documentation for accuracy
- [ ] Check for outdated screenshots/examples
- [ ] Update version numbers if applicable
- [ ] Verify all installation steps still work

### Quarterly Tasks

- [ ] Audit all documentation files
- [ ] Remove or archive outdated documents
- [ ] Consolidate redundant information
- [ ] Update architecture diagrams if changed

### Before Major Releases

- [ ] Full documentation review
- [ ] Update all version references
- [ ] Create/update CHANGELOG.md
- [ ] Verify deployment guide with fresh environment
- [ ] Update API documentation

---

## Consolidation Guidelines

### When to Consolidate

**Consolidate when you find:**

1. **Duplicate Information**
   ```
   ❌ Installation steps in README.md AND setup.md
   ✅ Installation steps in README.md, reference from setup.md
   ```

2. **Scattered Related Content**
   ```
   ❌ Deployment info in README, DEPLOY.md, and setup.md
   ✅ All deployment info in DEPLOYMENT_GUIDE.md
   ```

3. **Outdated Multiple Versions**
   ```
   ❌ README_v1.md, README_v2.md, README.md
   ✅ README.md (current), archive old versions in git history
   ```

### Consolidation Process

#### Step 1: Identify Overlap

Create a matrix of documentation coverage:

| Topic | README.md | DEPLOYMENT_GUIDE.md | Other Files |
|-------|-----------|---------------------|-------------|
| Installation | ✅ Quick | ✅ Detailed | ❌ |
| Architecture | ✅ Overview | ❌ | ❌ |
| Deployment | ✅ Summary | ✅ Complete | ⚠️ setup.md |
| API Docs | ✅ Summary | ❌ | ⚠️ api.md |

#### Step 2: Decide Primary Location

**Rules:**
- **README.md** = Overview + Quick Start only
- **DEPLOYMENT_GUIDE.md** = All build/deploy details
- **Separate guides** = Complex topics (API, architecture, contributing)

#### Step 3: Consolidate Content

```markdown
<!-- In README.md -->
## Deployment

For complete deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

Quick deploy:
\`\`\`bash
adk deploy agent_engine --project=$PROJECT_ID --region=us-central1 .
\`\`\`
```

#### Step 4: Remove Duplicates

```bash
# Archive old files (don't just delete)
git mv old_deploy_guide.md archive/old_deploy_guide.md
git commit -m "docs: Archive outdated deployment guide"

# Or delete if truly not needed
git rm redundant_readme.md
git commit -m "docs: Remove redundant documentation"
```

### Consolidation Rules

#### Rule 1: Single Source of Truth

**Each piece of information should exist in ONE primary location.**

Example:
```
Installation commands → DEPLOYMENT_GUIDE.md (primary)
README.md → Link to DEPLOYMENT_GUIDE.md
```

#### Rule 2: Progressive Disclosure

**README = Overview, Detailed docs = Deep dive**

```markdown
<!-- README.md -->
## Quick Start
1. Install: `pip install -r requirements.txt`
2. Configure: `cp .env.example .env`
3. Run: `python main.py`

For detailed setup, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

<!-- DEPLOYMENT_GUIDE.md -->
## Installation (Detailed)
1. Create virtual environment
2. Install system dependencies
3. Install Python packages
...
```

#### Rule 3: Clear Cross-References

**Use consistent linking format:**

```markdown
✅ See [API Documentation](docs/API.md#authentication) for details.
✅ Refer to the [Deployment Guide](DEPLOYMENT_GUIDE.md) for complete instructions.

❌ See other file for more info
❌ Check the deployment docs
```

---

## Version Control

### Git Best Practices for Documentation

#### Commit Messages

```bash
# Good commit messages for docs
git commit -m "docs: Add deployment troubleshooting section"
git commit -m "docs: Update API endpoint examples"
git commit -m "docs: Fix broken links in README"
git commit -m "docs: Consolidate installation guides"

# Bad commit messages
git commit -m "update docs"
git commit -m "fix"
git commit -m "changes"
```

#### Documentation-Specific .gitignore

Already configured in `.gitignore`:

```gitignore
# Knowledge Base (excluded as specified)
Knowledge_Base/
Prompt.md

# Generated documentation
docs/_build/
site/

# Temporary files
*.tmp
*~
.DS_Store
```

#### Branching for Major Doc Updates

```bash
# Create branch for major documentation overhaul
git checkout -b docs/consolidate-guides

# Make changes
# ...

# Commit and push
git commit -m "docs: Consolidate deployment guides into single source"
git push origin docs/consolidate-guides

# Create pull request for review
```

### Semantic Versioning for Documentation

When project uses versions:

```markdown
<!-- In README.md -->
**Documentation Version:** 1.2.0 (matches project v1.2.0)

## Version History
- v1.2.0 - Added Vertex AI deployment guide
- v1.1.0 - Added Chrome extension documentation
- v1.0.0 - Initial release
```

---

## Documentation Templates

### Template: New Feature Documentation

When adding a new feature, update docs using this checklist:

```markdown
## Feature: [Feature Name]

### What to Update

- [ ] README.md - Add to features list
- [ ] DEPLOYMENT_GUIDE.md - Add deployment steps if needed
- [ ] API docs - Add new endpoints/methods
- [ ] Code comments - Document new functions/classes
- [ ] Tests - Document test coverage
- [ ] CHANGELOG.md - Add to unreleased section

### Template

#### In README.md
\`\`\`markdown
### [Feature Name]

Brief description of what the feature does.

**Usage:**
\`\`\`bash
# Example command
\`\`\`

For details, see [Link to detailed docs].
\`\`\`

#### In DEPLOYMENT_GUIDE.md
(If feature requires deployment changes)
```

### Template: Deprecation Notice

```markdown
## ⚠️ DEPRECATED: [Feature/Method Name]

**Deprecated in:** v1.5.0
**Removed in:** v2.0.0 (planned)
**Reason:** [Brief explanation]

**Migration Path:**

\`\`\`python
# Old way (deprecated)
old_method()

# New way (recommended)
new_method()
\`\`\`

See [Migration Guide](docs/MIGRATION.md) for details.
```

### Template: Troubleshooting Entry

```markdown
### Issue: [Brief Description of Problem]

**Symptoms:**
- Error message: `[exact error]`
- When it occurs: [scenario]

**Cause:**
[Explanation of why this happens]

**Solution:**
\`\`\`bash
# Step-by-step fix
command1
command2
\`\`\`

**Prevention:**
[How to avoid this issue]
```

---

## Documentation Audit Checklist

### Monthly Audit

Use this checklist monthly:

```markdown
## Documentation Audit - [Month Year]

### Accuracy Check
- [ ] All installation commands work
- [ ] All code examples run without errors
- [ ] Version numbers are current
- [ ] Screenshots are up-to-date
- [ ] Links are not broken

### Completeness Check
- [ ] All features documented
- [ ] All API endpoints documented
- [ ] All configuration options explained
- [ ] Troubleshooting covers common issues

### Organization Check
- [ ] No duplicate content
- [ ] Logical structure
- [ ] Clear navigation
- [ ] Proper cross-references

### Cleanup
- [ ] Remove outdated files
- [ ] Archive superseded versions
- [ ] Update timestamps
- [ ] Fix formatting inconsistencies

### Actions Required
1. [List specific updates needed]
2. [...]
```

---

## Preventing Documentation Clutter

### Rules to Prevent Clutter

#### 1. One Topic, One File Rule

```
✅ One comprehensive DEPLOYMENT_GUIDE.md
❌ deploy.md, setup.md, installation.md, getting-started.md
```

#### 2. The 3-File Rule for Core Docs

**Core documentation should fit in 3 files:**
1. README.md (Overview)
2. DEPLOYMENT_GUIDE.md (How to build/run/deploy)
3. One additional file if needed (API reference, Architecture, etc.)

**Everything else goes in `docs/` subdirectory or is linked externally.**

#### 3. Archive, Don't Delete

```bash
# Instead of deleting
git rm old_guide.md  # ❌ Lost forever

# Archive it
mkdir -p archive/2024
git mv old_guide.md archive/2024/
git commit -m "docs: Archive old guide to history"  # ✅ Preserved
```

#### 4. Regular Cleanup Schedule

```bash
# Add to crontab or CI/CD
# Every quarter, run:

# Find docs not updated in 6+ months
find . -name "*.md" -type f -mtime +180 -exec ls -lh {} \;

# Review and archive or update
```

#### 5. Automated Link Checking

```bash
# Install markdown-link-check
npm install -g markdown-link-check

# Check all docs
find . -name "*.md" -exec markdown-link-check {} \;

# Add to CI/CD pipeline
```

---

## Integration with Development Workflow

### Pre-Commit Documentation Checks

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check for TODO/FIXME in docs
if git diff --cached --name-only | grep -q '\.md$'; then
    if git diff --cached | grep -E 'TODO|FIXME'; then
        echo "Warning: Documentation contains TODO/FIXME"
    fi
fi

# Check for Last Updated timestamp
CHANGED_DOCS=$(git diff --cached --name-only | grep '\.md$')
for doc in $CHANGED_DOCS; do
    if ! grep -q "Last Updated:" "$doc"; then
        echo "Warning: $doc missing 'Last Updated' timestamp"
    fi
done
```

### Documentation in Pull Requests

**PR template should include:**

```markdown
## Documentation Updates

- [ ] README.md updated (if feature visible to users)
- [ ] DEPLOYMENT_GUIDE.md updated (if deployment changes)
- [ ] Code comments added/updated
- [ ] API documentation updated (if API changes)
- [ ] No duplicate documentation created
```

---

## Tools & Automation

### Recommended Tools

1. **Linting**
   ```bash
   # Install markdownlint
   npm install -g markdownlint-cli

   # Lint all docs
   markdownlint **/*.md
   ```

2. **Link Checking**
   ```bash
   # Check for broken links
   markdown-link-check README.md DEPLOYMENT_GUIDE.md
   ```

3. **Documentation Generation**
   ```bash
   # Generate API docs from code
   pip install pdoc3
   pdoc --html agents/ models/ tools/ -o docs/api/
   ```

4. **Spell Checking**
   ```bash
   # Install aspell
   aspell check README.md
   ```

### Automation Scripts

Create `scripts/check-docs.sh`:

```bash
#!/bin/bash
# Documentation health check

echo "Checking documentation..."

# Check for broken links
echo "1. Checking links..."
markdown-link-check README.md DEPLOYMENT_GUIDE.md

# Check for outdated timestamps
echo "2. Checking timestamps..."
find . -name "*.md" -exec grep -L "Last Updated:" {} \;

# Lint markdown
echo "3. Linting markdown..."
markdownlint **/*.md

echo "Documentation check complete!"
```

---

## Contact & Support

For questions about documentation:
1. Check existing documentation first
2. Search closed issues on GitHub
3. Open a new issue with label `documentation`

---

**Last Updated:** 2025-01-15
