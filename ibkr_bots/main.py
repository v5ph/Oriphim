"""Project Market Watch — basic orchestrator.

Safe default behavior:
- Load config/universe.json
- Attempt IBKR (TWS) connection using ib_insync if installed
- Subscribe briefly to SPY/QQQ top-of-book market data as a smoke test
- No trading logic is executed

Run:
  python ibkr_bots/main.py
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List


def load_universe(path: str | os.PathLike) -> Dict[str, List[str]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging(log_dir: str | os.PathLike) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logfile = Path(log_dir) / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def ib_connect():
    """Return an IB instance if ib_insync is available, else None."""
    try:
        from ib_insync import IB
    except Exception:
        logging.warning("ib_insync not available; running without broker connectivity.")
        return None

    host = os.getenv("IB_HOST", "127.0.0.1")
    port = int(os.getenv("IB_PORT", "7497"))
    client_id = int(os.getenv("IB_CLIENT_ID", "2"))

    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=5)
        logging.info("IBKR connected: %s", ib.isConnected())
        return ib
    except Exception as e:
        logging.error("IBKR connection failed: %s", e)
        return None


def subscribe_example(ib) -> None:
    """Subscribe to SPY and QQQ quotes as a smoke test; cancel immediately."""
    if ib is None:
        return
    try:
        from ib_insync import Stock
        spy = Stock("SPY", "SMART", "USD")
        qqq = Stock("QQQ", "SMART", "USD")
        ib.qualifyContracts(spy, qqq)

        # Request top-of-book; cancel shortly after
        spy_ticker = ib.reqMktData(spy, "", False, False)
        qqq_ticker = ib.reqMktData(qqq, "", False, False)
        ib.sleep(1.0)
        logging.info("SPY bid/ask: %s / %s", spy_ticker.bid, spy_ticker.ask)
        logging.info("QQQ bid/ask: %s / %s", qqq_ticker.bid, qqq_ticker.ask)
        ib.cancelMktData(spy)
        ib.cancelMktData(qqq)
    except Exception as e:
        logging.warning("Market data subscription failed or not authorized: %s", e)


def main() -> int:
    root = Path(__file__).resolve().parent
    setup_logging(root / "logs")

    # Load universe
    universe_path = root / "config" / "universe.json"
    if universe_path.exists():
        universe = load_universe(universe_path)
        logging.info("Universe loaded: %s", {k: len(v) for k, v in universe.items()})
    else:
        logging.warning("Universe file missing at %s", universe_path)
        universe = {}

    # Connect to IBKR if possible
    ib = ib_connect()
    try:
        subscribe_example(ib)
    finally:
        try:
            if ib is not None:
                ib.disconnect()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
