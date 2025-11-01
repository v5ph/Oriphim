"""Quick IBKR connectivity check using ib_insync.

Usage:
  python -m ibkr_bots.connect_test

Environment variables (optional):
  IB_HOST (default: 127.0.0.1)
  IB_PORT (default: 7497)
  IB_CLIENT_ID (default: 1)
"""

import os
import sys


def main() -> int:
    try:
        from ib_insync import IB
    except Exception as e:
        print("ib_insync not installed or failed to import:", e)
        return 1

    host = os.getenv("IB_HOST", "127.0.0.1")
    port = int(os.getenv("IB_PORT", "7497"))
    client_id = int(os.getenv("IB_CLIENT_ID", "1"))

    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=5)
        print("Connected:", ib.isConnected())
        return 0 if ib.isConnected() else 2
    except Exception as e:
        print("Connection failed:", e)
        return 2
    finally:
        try:
            ib.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())

