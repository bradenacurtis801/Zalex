# Alembic Migration Best Practices

## Recommended Workflow

### 1. **Auto-generate Migrations (Recommended)**

This is the standard approach for most schema changes:

```bash
# 1. Make changes to your SQLModel models in backend/src/models/database.py
#    (e.g., add a field, change a constraint, etc.)

# 2. Generate migration automatically
cd backend
alembic revision --autogenerate -m "Description of changes"

# 3. Review the generated migration file
#    Check: backend/migrations/versions/XXX_description.py

# 4. Apply the migration
alembic upgrade head
```

**When to use:**
- Adding/removing columns
- Changing field types
- Adding/removing indexes
- Adding/removing constraints
- Most schema changes that can be detected automatically

### 2. **Manual Migrations (For Complex Cases)**

Sometimes you need to write migrations manually:

```bash
# Create an empty migration file
alembic revision -m "Description of changes"

# Then manually write the upgrade() and downgrade() functions
```

**When to use:**
- Data migrations (moving/transforming data)
- Complex SQL operations that autogenerate can't handle
- Custom PostgreSQL features (like the `DO $$` blocks we used)
- Operations that require multiple steps with data cleanup

## Example: Auto-generate Workflow

```bash
# Step 1: Modify your model
# In backend/src/models/database.py:
# - Add: unique=True to document_id field

# Step 2: Generate migration
cd backend
alembic revision --autogenerate -m "add unique constraint to document_id"

# Step 3: Review generated file
# Alembic will create something like:
# backend/migrations/versions/XXX_add_unique_constraint.py

# Step 4: Apply
alembic upgrade head
```

## Example: Manual Migration (Like We Did)

For our one-to-one migration, we needed to:
1. Delete duplicate data first
2. Then add the constraint

This required manual SQL, so we created it manually:

```bash
# Create empty migration
alembic revision -m "make classification one to one"

# Then manually write the upgrade/downgrade functions
```

## Best Practices

### ✅ DO:
- Use `--autogenerate` for most schema changes
- Always review generated migrations before applying
- Test migrations on a copy of production data first
- Write clear migration messages
- Include both `upgrade()` and `downgrade()` functions
- Keep migrations small and focused (one logical change per migration)

### ❌ DON'T:
- Edit existing migrations that have been applied to production
- Skip reviewing auto-generated migrations
- Create migrations manually when autogenerate would work
- Mix data migrations with schema migrations (split them up)

## Common Commands

```bash
# Generate auto-migration
alembic revision --autogenerate -m "description"

# Create empty migration (manual)
alembic revision -m "description"

# Apply all pending migrations
alembic upgrade head

# Apply one migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## For Your Current Case

Since you already have the model changes in `database.py`:
1. You could have used: `alembic revision --autogenerate -m "make classification one to one"`
2. But it wouldn't have handled the data cleanup (deleting duplicates)
3. So manual migration was the right choice here

## Next Time

For future schema changes:
1. Modify models in `database.py`
2. Run `alembic revision --autogenerate -m "your description"`
3. Review the generated file
4. Add any data migration steps if needed
5. Apply with `alembic upgrade head`

