#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Rede com vários nós: o bloco 1 do snapshot propaga, reorganização pela cadeia de mais trabalho e nó novo sincroniza do zero."""
import json
from decimal import Decimal

from test_framework.key import ECKey
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class PortgigaRedeTest(BitcoinTestFramework):
    def add_options(self, parser):
        self.add_wallet_options(parser, legacy=False)

    def set_test_params(self):
        self.num_nodes = 3
        self.setup_clean_chain = True

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def setup_network(self):
        self.setup_nodes()
        self.connect_nodes(0, 1)  # o nó 2 fica de fora até o fim

    def snapshot(self):
        n = self.nodes[0]
        saidas = []
        for valor in (12345678900, 98765432100):
            k = ECKey()
            k.generate()
            d = f"wpkh({k.get_pubkey().get_bytes().hex()})"
            d = d + "#" + n.getdescriptorinfo(d)["checksum"]
            saidas.append({"script": n.validateaddress(n.deriveaddresses(d)[0])["scriptPubKey"], "valor": valor})
        caminho = self.options.tmpdir + "/snapshot_rede.json"
        with open(caminho, "w") as fh:
            json.dump({"rede": "regtest", "saidas": saidas}, fh)
        return caminho

    def run_test(self):
        caminho = self.snapshot()
        for i in range(3):
            self.restart_node(i, [f"-snapshotteste={caminho}"])
        self.connect_nodes(0, 1)
        n0, n1, n2 = self.nodes

        self.log.info("Bloco 1 do snapshot propaga")
        if not n0.listwallets():
            n0.createwallet("w0")
        if not n1.listwallets():
            n1.createwallet("w1")
        a0 = n0.getnewaddress()
        self.generatetoaddress(n0, 1, a0, sync_fun=lambda: self.sync_blocks([n0, n1]))
        assert_equal(n1.getblockhash(1), n0.getblockhash(1))
        assert_equal(len(n1.getblock(n1.getblockhash(1), 2)["tx"][0]["vout"]), 3)  # 2 do snapshot + compromisso SegWit
        self.generatetoaddress(n0, 110, a0, sync_fun=lambda: self.sync_blocks([n0, n1]))

        self.log.info("Rede dividida: cada lado minera; ao juntar, vale a cadeia de mais trabalho")
        self.disconnect_nodes(0, 1)
        txid = n0.sendtoaddress(n1.getnewaddress(), Decimal("1"))
        self.generatetoaddress(n0, 2, a0, sync_fun=self.no_op)
        assert_equal(n0.gettransaction(txid)["confirmations"], 2)
        self.generatetoaddress(n1, 5, n1.getnewaddress(), sync_fun=self.no_op)
        self.connect_nodes(0, 1)
        self.sync_blocks([n0, n1])
        assert_equal(n0.getbestblockhash(), n1.getbestblockhash())
        assert_equal(n0.getblockcount(), 1 + 110 + 5)
        # a transação da cadeia perdida volta para a fila
        assert txid in n0.getrawmempool()

        self.log.info("Nó novo sincroniza do zero e confere o bloco 1")
        assert_equal(n2.getblockcount(), 0)
        self.connect_nodes(2, 0)
        self.sync_blocks()
        assert_equal(n2.getblockhash(1), n0.getblockhash(1))
        assert_equal(n2.getbestblockhash(), n0.getbestblockhash())


if __name__ == '__main__':
    PortgigaRedeTest(__file__).main()
