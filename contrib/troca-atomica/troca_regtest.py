#!/usr/bin/env python3
"""Prova de conceito: contrato HTLC (troca atômica) na rede Portgiga Core, só em REGTEST.

É o "lado PTG" de uma troca atômica PTG <-> BTC. O lado BTC usa exatamente o mesmo
script no Bitcoin (o portgiga-core é um fork do Bitcoin Core v29 com CLTV/SegWit/Taproot
ativos desde o bloco 1). Nenhum dinheiro real: regtest, moedas sem valor, nó local.

Script (P2WSH):
  OP_IF   OP_SHA256 <H> OP_EQUALVERIFY <pub_quem_recebe>
  OP_ELSE <T> OP_CHECKLOCKTIMEVERIFY OP_DROP <pub_quem_pagou>
  OP_ENDIF OP_CHECKSIG

Teste 1 (resgate): quem recebe gasta revelando o segredo S (sha256(S) = H);
  o segredo fica público na corrente, e é assim que a outra pessoa resgataria o BTC.
Teste 2 (reembolso): antes da altura T o reembolso é recusado; depois de T, é aceito.

Uso: python3 troca_regtest.py   (sobe e derruba um portgigad -regtest temporário)
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from decimal import Decimal

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "test", "functional"))

from test_framework.key import ECKey  # noqa: E402
from test_framework.messages import (  # noqa: E402
    COIN, COutPoint, CTransaction, CTxIn, CTxInWitness, CTxOut, tx_from_hex)
from test_framework.script import (  # noqa: E402
    CScript, OP_CHECKLOCKTIMEVERIFY, OP_CHECKSIG, OP_DROP, OP_ELSE, OP_ENDIF,
    OP_EQUALVERIFY, OP_IF, OP_SHA256, SIGHASH_ALL, SegwitV0SignatureMsg, hash256)
from test_framework.script_util import script_to_p2wsh_script  # noqa: E402
from test_framework.segwit_addr import encode_segwit_address  # noqa: E402

BIN = os.path.join(RAIZ, "build", "bin")
PORTA_RPC = 29787


class No:
    def __init__(self, porta=PORTA_RPC, p2p=29777, hrp="bcrt", bindir=BIN, daemon="portgigad", cli="portgiga-cli", nome="PTG"):
        self.hrp, self.nome = hrp, nome
        self.cli = os.path.join(bindir, cli)
        self.dir = tempfile.mkdtemp(prefix="ptg-regtest-")
        self.args = [f"-datadir={self.dir}", "-regtest", f"-rpcport={porta}",
                     "-rpcuser=t", "-rpcpassword=t"]
        subprocess.run([os.path.join(bindir, daemon), *self.args, "-daemon",
                        "-fallbackfee=0.0001", "-txindex=1", "-listen=0", f"-port={p2p}"],
                       check=True, stdout=subprocess.DEVNULL)
        for _ in range(60):
            try:
                self("getblockchaininfo")
                return
            except subprocess.CalledProcessError:
                time.sleep(0.5)
        raise SystemExit(f"{daemon} não subiu")

    def __call__(self, metodo, *params, carteira=None):
        cmd = [self.cli, *self.args]
        if carteira:
            cmd.append(f"-rpcwallet={carteira}")
        cmd += [metodo, *[p if isinstance(p, str) else json.dumps(p) for p in params]]
        saida = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
        try:
            return json.loads(saida, parse_float=Decimal)
        except json.JSONDecodeError:
            return saida

    def tenta(self, metodo, *params):
        try:
            return True, self(metodo, *params)
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def minerar(self, n):
        return self("generatetoaddress", n, self("getnewaddress", carteira="a"))

    def destino(self):
        return bytes.fromhex(self("getaddressinfo", self("getnewaddress", carteira="a"),
                                  carteira="a")["scriptPubKey"])

    def chave(self):
        k = ECKey(); k.generate()
        return type("Chave", (), {"k": k, "pub": k.get_pubkey().get_bytes()})

    def parar(self):
        try:
            self("stop")
            time.sleep(2)
        finally:
            shutil.rmtree(self.dir, ignore_errors=True)


def htlc(h, pub_recebe, pub_paga, t):
    return CScript([OP_IF, OP_SHA256, h, OP_EQUALVERIFY, pub_recebe,
                    OP_ELSE, t, OP_CHECKLOCKTIMEVERIFY, OP_DROP, pub_paga,
                    OP_ENDIF, OP_CHECKSIG])


def travar(no, script, valor):
    return travar_em(no, script, valor)


def travar_em(no, script, valor):
    """Manda `valor` para o endereço do contrato. Devolve (endereço, txid, vout, valor_sat)."""
    spk = script_to_p2wsh_script(script)
    endereco = encode_segwit_address(no.hrp, 0, hashlib.sha256(script).digest())
    txid = no("sendtoaddress", endereco, str(valor), carteira="a")
    no("generatetoaddress", 1, no("getnewaddress", carteira="a"))
    tx = no("getrawtransaction", txid, True)
    for o in tx["vout"]:
        if o["scriptPubKey"]["hex"] == spk.hex():
            return endereco, txid, o["n"], int(o["value"] * COIN)
    raise RuntimeError("saída do contrato não encontrada")


def gastar(script, txid, vout, valor_sat, destino_spk, chave, pilha, locktime=0):
    tx = CTransaction()
    tx.nLockTime = locktime
    tx.vin = [CTxIn(COutPoint(int(txid, 16), vout), nSequence=0xfffffffe)]
    tx.vout = [CTxOut(valor_sat - 2000, destino_spk)]  # 2000 sat de taxa
    sighash = hash256(SegwitV0SignatureMsg(script, tx, 0, SIGHASH_ALL, valor_sat))
    assinatura = chave.sign_ecdsa(sighash) + bytes([SIGHASH_ALL])
    tx.wit.vtxinwit = [CTxInWitness()]
    tx.wit.vtxinwit[0].scriptWitness.stack = [assinatura, *pilha, bytes(script)]
    return tx.serialize().hex()


def main():
    no = No()
    try:
        no("createwallet", "a")
        no("generatetoaddress", 101, no("getnewaddress", carteira="a"))
        print(f"rede regtest no ar, altura {no('getblockcount')}, saldo "
              f"{no('getbalance', carteira='a')} PTG de teste")

        ana, beto = ECKey(), ECKey()   # Ana paga em PTG, Beto pagaria em BTC
        ana.generate(); beto.generate()
        destino_beto = bytes.fromhex(no("getaddressinfo", no("getnewaddress", carteira="a"),
                                        carteira="a")["scriptPubKey"])

        # ---- Teste 1: resgate com o segredo ----
        segredo = os.urandom(32)
        h = hashlib.sha256(segredo).digest()
        t = no("getblockcount") + 20
        s = htlc(h, beto.get_pubkey().get_bytes(), ana.get_pubkey().get_bytes(), t)
        end, txid, vout, sat = travar(no, s, "5")
        print(f"\n[1] Ana travou 5 PTG no contrato {end}")
        errado = gastar(s, txid, vout, sat, destino_beto, beto, [os.urandom(32), b"\x01"])
        ok, msg = no.tenta("sendrawtransaction", errado)
        print(f"    Beto com segredo ERRADO: {'ACEITO (falha!)' if ok else 'recusado ✔'}  ({msg[:60]})")
        assert not ok
        certo = gastar(s, txid, vout, sat, destino_beto, beto, [segredo, b"\x01"])
        resg = no("sendrawtransaction", certo)
        no("generatetoaddress", 1, no("getnewaddress", carteira="a"))
        print(f"    Beto com segredo certo: aceito ✔ tx {resg[:16]}…")
        pilha = no("getrawtransaction", resg, True)["vin"][0]["txinwitness"]
        visto = bytes.fromhex(pilha[1])
        assert visto == segredo
        print(f"    segredo lido da corrente pela Ana: {visto.hex()[:16]}… = o mesmo ✔"
              "\n    (com ele a Ana resgataria o BTC do contrato gêmeo no Bitcoin)")

        # ---- Teste 2: reembolso por tempo ----
        segredo2 = os.urandom(32)
        t2 = no("getblockcount") + 10
        s2 = htlc(hashlib.sha256(segredo2).digest(), beto.get_pubkey().get_bytes(),
                  ana.get_pubkey().get_bytes(), t2)
        end2, txid2, vout2, sat2 = travar(no, s2, "3")
        print(f"\n[2] Ana travou 3 PTG, prazo até o bloco {t2} (agora {no('getblockcount')})")
        reemb = gastar(s2, txid2, vout2, sat2, destino_beto, ana, [b""], locktime=t2)
        ok, msg = no.tenta("sendrawtransaction", reemb)
        print(f"    reembolso ANTES do prazo: {'ACEITO (falha!)' if ok else 'recusado ✔'}  ({msg[:60]})")
        assert not ok
        no("generatetoaddress", t2 - no("getblockcount"), no("getnewaddress", carteira="a"))
        ok, msg = no.tenta("sendrawtransaction", reemb)
        print(f"    reembolso DEPOIS do prazo (bloco {no('getblockcount')}): "
              f"{'aceito ✔' if ok else 'RECUSADO (falha!) ' + msg}")
        assert ok
        print("\nTUDO CERTO: o contrato de troca atômica funciona na Portgiga Core (regtest).")
    finally:
        no.parar()


if __name__ == "__main__":
    main()
