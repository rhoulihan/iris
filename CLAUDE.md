# Claude Code Session Notes

This file contains important notes and context for Claude Code sessions.

## Frontend CI Setup (2025-11-22)

### GitHub Actions Configuration
The frontend pre-commit hooks require Node.js and npm dependencies to be installed in CI:

**Required workflow steps** (.github/workflows/test.yml):
```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

- name: Install frontend dependencies
  run: |
    cd frontend
    npm ci
```

These steps must be added **before** the "Run pre-commit hooks" step, otherwise frontend hooks (prettier, eslint, svelte-check, npm audit) will fail with "command not found" errors.

### ESLint Disable Comments with Prettier

When using `eslint-disable-next-line` comments in TypeScript files that are formatted by Prettier:

**Issue**: Prettier reformats code and can separate the disable comment from the line it's meant to suppress.

**Solution**: Place the disable comment **directly before** the problematic line:
```typescript
// Correct placement - comment stays with the line
const hostnameRegex =
  // eslint-disable-next-line security/detect-unsafe-regex
  /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
```

**Don't do this** (prettier may move it):
```typescript
// eslint-disable-next-line security/detect-unsafe-regex
const hostnameRegex =
  /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
```

### Frontend Security Scanning

The frontend has the following security measures:
- **eslint-plugin-security**: Detects ReDoS, unsafe regex, object injection
- **npm audit**: Scans dependencies for vulnerabilities (high/critical only)
- **Safe regex patterns**: Using bounded quantifiers `{0,61}` to prevent ReDoS attacks
- **Bounds checking**: Array access validated with `Math.min()` before indexing

Example from validators.ts:
- Hostname validation uses bounded quantifiers and length check
- Regex is documented as safe to prevent false positives
- ESLint warning suppressed with justification

## Current Status

### Frontend (Sprint 1.1 Complete)
- ✅ Svelte 5 + SvelteKit initialized
- ✅ Tailwind CSS v4 + DaisyUI v5 configured
- ✅ TypeScript strict mode enabled
- ✅ ESLint v9 + Prettier configured
- ✅ Security scanning active
- ✅ Pre-commit hooks working (local and CI)
- ✅ Production build verified (0 errors)
- ✅ Code Quality Checks passing in GitHub Actions

### Backend
- ⚠️ Integration test failing: `test_product_catalog_lob_cliff_high_severity`
  - Location: tests/integration/test_end_to_end_pattern_detection.py:299
  - Issue: LOB cliff pattern detected with MEDIUM severity instead of HIGH
  - Needs investigation in LOBCliffDetector severity calculation logic

## Git Tips

### Working Directory Management
- Repository can have multiple sub-git repositories (e.g., frontend/)
- Always verify `pwd` when running git commands
- Use full paths from repo root when needed
- Bash `cd` command doesn't persist across separate tool calls

### Pre-commit Hooks
- Hooks may modify files during commit (prettier, eslint --fix)
- If files are modified by hooks, you need to stage them again
- The commit will fail if hooks modify files - this is expected behavior
- Re-stage modified files and commit again
