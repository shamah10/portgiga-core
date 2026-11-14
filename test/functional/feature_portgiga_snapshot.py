#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Snapshot no bloco 1: o coinbase tem que ser exatamente a lista; parcelas só podem ser gastas na data."""
import json
import time
from decimal import Decimal

from test_framework.blocktools import add_witness_commitment, create_block, create_coinbase
from test_framework.key import ECKey
from test_framework.messages import COIN, CTxOut
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error
from test_framework.wallet_util import bytes_to_wif

DIA = 24 * 3600


class PortgigaSnapshotTest(BitcoinTestFramework):
    def add_options(self, parser):
        self.add_wallet_options(parser, legacy=False)

    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def desc(self, d):
        """Descritor com checksum, mantendo chaves privadas (getdescriptorinfo devolve a forma pública)."""
        return d + "#" + self.nodes[0].getdescriptorinfo(d)["checksum"]

    def script_de(self, d):
        endereco = self.nodes[0].deriveaddresses(self.desc(d))[0]
        return self.nodes[0].validateaddress(endereco)["scriptPubKey"]

    def montar_snapshot(self):
        n = self.nodes[0]
        self.inicio = int(time.time())  # o gênese da regtest é de 2011: as datas partem de agora
        self.chaves = {}
        for nome in ("dono", "premios", "antiga"):
            k = ECKey()
            k.generate()
            self.chaves[nome] = k
        pub = lambda nome: self.chaves[nome].get_pubkey().get_bytes().hex()
        saidas = [
            {"tipo": "livre", "descritor": f"wpkh({pub('dono')})", "valor": 527184656165},
            {"tipo": "livre", "descritor": f"wpkh({pub('premios')})", "valor": 99900000000},
            {"tipo": "livre", "descritor": f"wpkh({pub('antiga')})", "valor": 1000000},
        ]
        self.desde = [self.inicio + 30 * DIA * (i + 1) for i in range(48)]
        for i, t in enumerate(self.desde):
            saidas.append({"tipo": "parcela", "parcela": i + 1, "desde": t, "descritor": f"wsh(and_v(v:pk({pub('dono')}),after({t})))", "valor": 100000000})
        for s in saidas:
            s["script"] = self.script_de(s["descritor"])
        self.saidas = saidas
        caminho = self.nodes[0].datadir_path / "snapshot_teste.json"
        caminho.write_text(json.dumps({"rede": "regtest", "altura_antiga": 0, "lancamento": "teste", "saidas": saidas}))
        return caminho

    def bloco1(self, alterar):
        n = self.nodes[0]
        tip = n.getbestblockhash()
        cb = create_coinbase(1)
        cb.vout = [CTxOut(s["valor"], bytes.fromhex(s["script"])) for s in self.saidas]
        alterar(cb.vout)
        cb.rehash()
        b = create_block(int(tip, 16), cb, n.getblock(tip)["time"] + 1)
        add_witness_commitment(b)
        b.solve()
        return b.serialize().hex()

    def run_test(self):
        n = self.nodes[0]
        caminho = self.montar_snapshot()
        self.restart_node(0, [f"-snapshotteste={caminho}"])
        n = self.nodes[0]

        self.log.info("Bloco 1 diferente da lista é recusado")
        extra = lambda v: v.append(CTxOut(1, bytes.fromhex(self.saidas[0]["script"])))
        falta = lambda v: v.pop()
        valor = lambda v: setattr(v[0], "nValue", v[0].nValue + 1)
        ordem = lambda v: v.reverse()
        for alterar in (extra, falta, valor, ordem):
            assert_equal(n.submitblock(self.bloco1(alterar)), "bad-portgiga-snapshot")
        assert_equal(n.getblockcount(), 0)

        self.log.info("O minerador monta o bloco 1 com a lista")
        if not n.listwallets():
            n.createwallet("w")
        destino = n.getnewaddress()
        self.generatetoaddress(n, 1, destino)
        cb = n.getblock(n.getbestblockhash(), 2)["tx"][0]
        saidas_cb = [v for v in cb["vout"] if not v["scriptPubKey"]["hex"].startswith("6a24aa21a9ed")]
        assert_equal([v["scriptPubKey"]["hex"] for v in saidas_cb], [s["script"] for s in self.saidas])
        assert_equal([int(v["value"] * COIN) for v in saidas_cb], [s["valor"] for s in self.saidas])

        self.log.info("Parte livre: gastável depois de 100 blocos")
        n.createwallet("dono", blank=True)
        dono = n.get_wallet_rpc("dono")
        wif = bytes_to_wif(self.chaves["dono"].get_bytes())
        res = dono.importdescriptors([{"desc": self.desc(f"wpkh({wif})"), "timestamp": 0}])
        assert res[0]["success"], res
        self.generatetoaddress(n, 100, destino)
        dono.sendall([destino])  # carteira só com a chave importada: sem endereço de troco
        self.generatetoaddress(n, 1, destino)

        self.log.info("Parcela 1: travada até a data")
        cbtxid = cb["txid"]
        pos = 3  # primeira parcela
        t1 = self.desde[0]
        wsh = f"wsh(and_v(v:pk({wif}),after({t1})))"
        res = dono.importdescriptors([{"desc": self.desc(wsh), "timestamp": 0}])
        assert res[0]["success"], res

        def gasto(locktime):
            raw = n.createrawtransaction([{"txid": cbtxid, "vout": pos, "sequence": 0xfffffffe}], [{destino: Decimal("0.9999")}], locktime)
            return dono.signrawtransactionwithwallet(raw)

        assinada = gasto(t1)
        assert assinada["complete"], assinada
        assert_raises_rpc_error(-26, "non-final", n.sendrawtransaction, assinada["hex"])
        # locktime antes da data não satisfaz o CHECKLOCKTIMEVERIFY
        assert not gasto(t1 - 1)["complete"]

        self.log.info("Na data (MTP passou), a parcela 1 é gasta; a 2 continua travada")
        n.setmocktime(t1 + 2 * 3600)
        for _ in range(12):
            self.generatetoaddress(n, 1, destino)
        assert n.getblock(n.getbestblockhash())["mediantime"] >= t1
        n.sendrawtransaction(assinada["hex"])
        self.generatetoaddress(n, 1, destino)
        t2 = self.desde[1]
        raw2 = n.createrawtransaction([{"txid": cbtxid, "vout": pos + 1, "sequence": 0xfffffffe}], [{destino: Decimal("0.9999")}], t2)
        dono.importdescriptors([{"desc": self.desc(f"wsh(and_v(v:pk({wif}),after({t2})))"), "timestamp": 0}])
        assinada2 = dono.signrawtransactionwithwallet(raw2)
        assert assinada2["complete"]
        assert_raises_rpc_error(-26, "non-final", n.sendrawtransaction, assinada2["hex"])


if __name__ == '__main__':
    PortgigaSnapshotTest(__file__).main()
