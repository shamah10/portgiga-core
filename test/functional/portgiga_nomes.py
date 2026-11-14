#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""O nó se apresenta como Portgiga na rede."""
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class PortgigaNomesTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1

    def run_test(self):
        sub = self.nodes[0].getnetworkinfo()["subversion"]
        assert sub.startswith("/Portgiga:"), sub
        assert_equal(self.nodes[0].getnetworkinfo()["localservicesnames"].count("NETWORK"), 1)


if __name__ == '__main__':
    PortgigaNomesTest(__file__).main()
