#!/usr/bin/env python3
"""
IBKR Connection Test

Quick test to verify IBKR TWS/Gateway connectivity and basic functionality.
Run this before starting the main trading bots.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.broker import get_broker
    from core.telemetry import get_telemetry_manager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('connection_test')


def test_broker_connection():
    """Test basic broker connectivity"""
    print("🔌 Testing IBKR broker connection...")
    
    broker = get_broker()
    
    # Get connection parameters
    host = os.getenv('IB_HOST', '127.0.0.1')
    port = int(os.getenv('IB_PORT', '7497'))
    client_id = int(os.getenv('IB_CLIENT_ID', '1'))
    
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Client ID: {client_id}")
    
    # Attempt connection
    success = broker.connect(host, port, client_id)
    
    if success:
        print("✅ Connection successful!")
        
        # Test basic functionality
        try:
            accounts = broker.ib.managedAccounts()
            print(f"   Managed accounts: {accounts}")
            
            # Test market data
            print("📊 Testing market data...")
            snapshot = broker.get_market_snapshot('SPY')
            
            if snapshot:
                print(f"   SPY Price: ${snapshot.price:.2f}")
                print(f"   Bid/Ask: ${snapshot.bid:.2f} / ${snapshot.ask:.2f}")
                print("✅ Market data working")
            else:
                print("⚠️  Market data not available (may be outside market hours)")
            
        except Exception as e:
            print(f"⚠️  Warning during extended tests: {e}")
        
        # Disconnect
        broker.disconnect()
        print("✅ Disconnected cleanly")
        return True
        
    else:
        print("❌ Connection failed!")
        print("\nTroubleshooting:")
        print("1. Ensure IBKR TWS or IB Gateway is running")
        print("2. Check API settings in TWS:")
        print("   - Global Config → API → Settings")
        print("   - Enable 'Socket Clients'")
        print("   - Verify port number (7497 for paper, 7496 for live)")
        print("3. Ensure no firewall blocking localhost connections")
        return False


def test_database():
    """Test database connectivity"""
    print("\n💾 Testing database connectivity...")
    
    try:
        telemetry = get_telemetry_manager()
        
        # Test logging a simple decision
        test_decision = {
            'symbol': 'TEST',
            'strategy': 'connection_test',
            'decision': 'TEST',
            'reason': 'Connection test',
            'filters': {'test': True},
            'market_data': {'price': 100.0}
        }
        
        telemetry.log_decision(test_decision)
        print("✅ Database write successful")
        
        # Test reading decisions
        decisions = telemetry.get_todays_decisions()
        print(f"   Found {len(decisions)} decisions today")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_config_files():
    """Test configuration file loading"""
    print("\n⚙️  Testing configuration files...")
    
    config_files = [
        'config/strategy.yaml',
        'config/universe.json',
        'config/.env.example'
    ]
    
    all_good = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} - missing")
            all_good = False
    
    # Test YAML loading
    try:
        import yaml
        with open('config/strategy.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ strategy.yaml loads correctly")
        
        # Check key settings
        mode = config.get('mode', 'unknown')
        print(f"   Mode: {mode}")
        
    except Exception as e:
        print(f"❌ Error loading strategy.yaml: {e}")
        all_good = False
    
    return all_good


def main():
    """Run all connection tests"""
    print("🚀 IBKR Options Bot - Connection Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test results
    tests = []
    
    # Test config files first
    config_ok = test_config_files()
    tests.append(('Configuration', config_ok))
    
    # Test database
    db_ok = test_database()
    tests.append(('Database', db_ok))
    
    # Test broker connection
    broker_ok = test_broker_connection()
    tests.append(('Broker Connection', broker_ok))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    
    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! System is ready for trading.")
        print("\nNext steps:")
        print("1. Start paper trading: bash scripts/run_paper.sh")
        print("2. Open dashboard: streamlit run dashboards/app.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please resolve issues before trading.")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)