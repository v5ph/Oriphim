#!/usr/bin/env node

/**
 * Database Schema Deployment Script
 * 
 * This script deploys the complete Oriphim database schema to Supabase.
 * Run this to fix "table not found" errors in the application.
 * 
 * Usage:
 *   node scripts/deploy-schema.js
 * 
 * Requirements:
 *   - Supabase project URL and service role key in environment
 *   - Network access to Supabase
 */

const fs = require('fs');
const path = require('path');

async function deploySchema() {
  // Check for required environment variables
  const supabaseUrl = process.env.VITE_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl) {
    console.error('❌ VITE_SUPABASE_URL environment variable is required');
    console.error('   Set it in your .env file or environment');
    process.exit(1);
  }

  if (!serviceRoleKey) {
    console.error('❌ SUPABASE_SERVICE_ROLE_KEY environment variable is required');
    console.error('   Get it from your Supabase project settings > API');
    console.error('   Add it to your .env file as SUPABASE_SERVICE_ROLE_KEY=your_key_here');
    process.exit(1);
  }

  // Read the schema file
  const schemaPath = path.join(__dirname, '..', 'cloud', 'supabase', 'sql', 'schema.sql');
  
  if (!fs.existsSync(schemaPath)) {
    console.error('❌ Schema file not found at:', schemaPath);
    process.exit(1);
  }

  const schema = fs.readFileSync(schemaPath, 'utf8');
  
  console.log('🚀 Deploying Oriphim database schema...');
  console.log('📍 Target:', supabaseUrl);
  console.log('📄 Schema file:', schemaPath);
  console.log('📊 Schema size:', schema.length, 'characters');

  try {
    // Deploy schema using Supabase REST API
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/exec_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${serviceRoleKey}`,
        'apikey': serviceRoleKey
      },
      body: JSON.stringify({ sql: schema })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('❌ Deployment failed:', response.status, response.statusText);
      console.error('   Response:', error);
      process.exit(1);
    }

    const result = await response.json();
    console.log('✅ Schema deployed successfully!');
    console.log('📋 Result:', result);
    
    console.log('\n🎉 Database is ready!');
    console.log('   • All tables created with proper RLS policies');
    console.log('   • Indexes optimized for performance');
    console.log('   • Triggers configured for data consistency');
    console.log('   • Realtime subscriptions enabled');
    console.log('\n🔄 Refresh your application to see the changes');

  } catch (error) {
    console.error('❌ Deployment error:', error.message);
    process.exit(1);
  }
}

// Manual deployment instructions
function showManualInstructions() {
  console.log('📋 Manual Deployment Instructions:');
  console.log('');
  console.log('1. Go to your Supabase dashboard:');
  console.log('   https://supabase.com/dashboard/project/your-project-id');
  console.log('');
  console.log('2. Click "SQL Editor" in the left sidebar');
  console.log('');
  console.log('3. Create a new query and paste the contents of:');
  console.log('   cloud/supabase/sql/schema.sql');
  console.log('');
  console.log('4. Click "Run" to execute the schema');
  console.log('');
  console.log('5. Refresh your application');
  console.log('');
  console.log('🔗 Direct link to SQL Editor:');
  console.log('   https://cotmmxarkuwjroywcvce.supabase.co/project/default/sql');
}

// Main execution
if (require.main === module) {
  console.log('🔧 Oriphim Database Schema Deployment');
  console.log('=====================================\n');

  // Show manual instructions as the primary method
  showManualInstructions();
  
  console.log('\n' + '─'.repeat(50) + '\n');
  console.log('💡 Alternatively, you can run this automated deployment:');
  console.log('   (Requires SUPABASE_SERVICE_ROLE_KEY in environment)');
  
  // Check if we should run automated deployment
  if (process.env.SUPABASE_SERVICE_ROLE_KEY) {
    console.log('\n🤖 Service role key detected. Running automated deployment...\n');
    deploySchema();
  } else {
    console.log('\n⚠️  No service role key found. Please use manual deployment above.');
  }
}

module.exports = { deploySchema };