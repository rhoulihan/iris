# Claude Code Session Notes

This file contains important notes and context for Claude Code sessions.

## Current Status

### Backend
- ⚠️ Integration test failing: `test_product_catalog_lob_cliff_high_severity`
  - Location: tests/integration/test_end_to_end_pattern_detection.py:299
  - Issue: LOB cliff pattern detected with MEDIUM severity instead of HIGH
  - Needs investigation in LOBCliffDetector severity calculation logic

## Git Tips

### Working Directory Management
- Always verify `pwd` when running git commands
- Use full paths from repo root when needed
- Bash `cd` command doesn't persist across separate tool calls

### Pre-commit Hooks
- Hooks may modify files during commit (e.g., black, isort)
- If files are modified by hooks, you need to stage them again
- The commit will fail if hooks modify files - this is expected behavior
- Re-stage modified files and commit again
