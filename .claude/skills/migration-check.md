---
name: migration-check
description: Verify alembic migration state before deployment — checks for pending migrations and validates head consistency
disable-model-invocation: true
---

## Migration Check

Run pre-deployment migration verification:

1. Check current migration head:
   ```bash
   cd backend && uv run alembic heads
   ```

2. Check for pending migrations:
   ```bash
   cd backend && uv run alembic check
   ```

3. If migrations are pending, show the diff:
   ```bash
   cd backend && uv run alembic history -r current:head
   ```

4. Report status:
   - If clean: "Migrations are up to date"
   - If pending: List pending migrations and ask for confirmation before proceeding
   - If head mismatch: Flag as error — multiple heads indicate a merge conflict in migrations
