#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""A prova de trabalho usa o hash personalizado: um bloco que só atende o alvo pelo hash do Bitcoin é recusado."""
from test_framework.blocktools import create_block, create_coinbase
from test_framework.messages import uint256_from_compact
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class PortgigaPowTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        n = self.nodes[0]
        self.generate(n, 10)
        assert_equal(n.getblockcount(), 10)

        tip = n.getbestblockhash()
        altura = n.getblockcount() + 1
        bloco = create_block(int(tip, 16), create_coinbase(altura), n.getblock(tip)["time"] + 1)
        alvo = uint256_from_compact(bloco.nBits)
        # procura um nonce em que o hash do Bitcoin passa e o da Portgiga não
        while not (bloco.sha256 <= alvo and bloco.pow_hash() > alvo):
            bloco.nNonce += 1
            bloco.rehash()
        assert_equal(n.submitblock(bloco.serialize().hex()), "high-hash")

        # e o mesmo bloco resolvido pelo hash da Portgiga é aceito
        bloco.solve()
        assert_equal(n.submitblock(bloco.serialize().hex()), None)
        assert_equal(n.getbestblockhash(), bloco.hash)


if __name__ == '__main__':
    PortgigaPowTest(__file__).main()
