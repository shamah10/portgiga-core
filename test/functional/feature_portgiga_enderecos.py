#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Endereços da Portgiga: prefixo tptg na rede de teste, e endereços do Bitcoin são recusados."""
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class PortgigaEnderecosTest(BitcoinTestFramework):
    def add_options(self, parser):
        self.add_wallet_options(parser, legacy=False)

    def set_test_params(self):
        self.num_nodes = 1
        self.chain = "testnet3"
        self.setup_clean_chain = True

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def run_test(self):
        n = self.nodes[0]
        if not n.listwallets():
            n.createwallet("w")
        assert n.getnewaddress("", "bech32").startswith("tptg1q")
        assert n.getnewaddress("", "bech32m").startswith("tptg1p")
        # endereço válido do Bitcoin (testnet) não vale na Portgiga
        assert_equal(n.validateaddress("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx")["isvalid"], False)
        assert_equal(n.getblockchaininfo()["chain"], "test")


if __name__ == '__main__':
    PortgigaEnderecosTest(__file__).main()
