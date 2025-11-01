"""Trading bot modules for Project Market Watch.

This package contains strategy-specific bots:
- Bot A: PUT-Lite (intraday premium harvesting)
- Bot B: Micro Buy-Write (covered calls)
- Bot C: Calm-Tape Condor (iron condors)

All bots should default to dry-run behavior and only place orders
when explicitly instructed by the caller.
"""

