#!/usr/bin/env python3
"""Inicia o ElectrumX já conhecendo a Portgiga.

  COIN=Portgiga NET=mainnet DB_ENGINE=leveldb DB_DIRECTORY=... DAEMON_URL=... \
  SERVICES=tcp://:50701,rpc://127.0.0.1:8000 python3 electrumx_portgiga.py

Para regtest, PTG_GENESIS=<getblockhash 0> define o gênese (cada regtest é diferente).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portgiga_coin  # noqa: E402,F401  (registra as classes)

if os.environ.get("PTG_GENESIS"):
    portgiga_coin.PortgigaRegtest.GENESIS_HASH = os.environ["PTG_GENESIS"]

from electrumx.cli.electrumx_server import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
