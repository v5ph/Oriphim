# Database Migration Instructions

## To Deploy Missing Tables to Supabase

### Option 1: Using Supabase SQL Editor (Recommended)
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `add_missing_tables_migration.sql`
4. Click "Run" to execute the migration

### Option 2: Using Supabase CLI
```bash
# Make sure you're in the cloud/supabase directory
cd cloud/supabase

# Push the updated schema
supabase db push

# Or apply the migration directly
supabase db reset --db-url "your-database-url"
```

### Option 3: Manual Table Creation
If you prefer to create tables one by one, you can run these commands in the SQL editor:

1. **Waitlist Table** (for email collection)
2. **Contact Messages Table** (for support messages) 
3. **Alert Preferences Table** (for user notification settings)

## What This Migration Adds

### ✅ New Tables:
- `waitlist` - Email collection for signup waitlist
- `contact_messages` - Customer support message storage
- `alert_preferences` - User notification preferences

### ✅ Security Features:
- Row Level Security (RLS) policies for data isolation
- Email format validation constraints
- Message length validation
- Proper foreign key relationships

### ✅ Performance Optimizations:
- Indexes on frequently queried columns
- Realtime subscriptions for live updates

### ✅ User Experience:
- Automatic alert preferences creation for new users
- Default notification settings
- Proper error handling

## Testing the Migration

After running the migration, you can test it by:

1. **Check Tables Exist:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('waitlist', 'contact_messages', 'alert_preferences');
```

2. **Test Waitlist Insert:**
```sql
INSERT INTO waitlist (email) VALUES ('test@example.com');
```

3. **Test Contact Message Insert:**
```sql
INSERT INTO contact_messages (name, email, message) 
VALUES ('Test User', 'test@example.com', 'This is a test message from the migration.');
```

4. **Check RLS Policies:**
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('alert_preferences');
```

## Next Steps

Once the migration is complete, you can:
1. ✅ Update frontend forms to use real database insertions
2. ✅ Test authentication flow with alert preferences creation
3. ✅ Implement notification system with alert preferences

The frontend is already configured with TypeScript types for these tables in `src/lib/supabase.ts`.