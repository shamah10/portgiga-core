#!/usr/bin/env python3
"""Troca atômica completa entre DUAS redes da família Bitcoin (HTLC SHA-256 + CLTV).

Qualquer nó compatível com o RPC do Bitcoin Core serve de cada lado:
portgigad (PTG), litecoind (LTC), bitcoind (BTC)... O protocolo:
  1. Ana sorteia S, publica H = sha256(S).
  2. Ana trava X na rede A: "Beto leva com S; senão volta para Ana após T_A".
  3. Beto confere e trava Y na rede B: "Ana leva com S; senão volta para Beto após T_B" (T_B < T_A).
  4. Ana resgata Y na rede B revelando S.
  5. Beto lê S da corrente B e resgata X na rede A.

`python3 troca_atomica.py --ensaio` roda a troca inteira entre dois portgigad -regtest
(o segundo faz o papel da "outra moeda"). Só redes de teste. Nada de dinheiro real.
Para LTC/BTC de verdade em testnet: criar Rede(cli=..., args=[...], hrp="tltc"/"tb").
"""
import hashlib, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from troca_regtest import No, htlc, gastar, travar_em  # noqa: E402


def trocar(a, b, x, y, margem_a=30, margem_b=15, log=print):
    """a, b: objetos No (já com carteira 'a' e saldo). Devolve True se a troca completou."""
    ana_a, ana_b = a.chave(), b.chave()   # Ana: paga em A, recebe em B
    beto_a, beto_b = a.chave(), b.chave() # Beto: paga em B, recebe em A
    s = os.urandom(32)
    h = hashlib.sha256(s).digest()
    log(f"1) Ana sorteou o segredo; H = {h.hex()[:16]}…")

    t_a = a("getblockcount") + margem_a
    sa = htlc(h, beto_a.pub, ana_a.pub, t_a)
    end_a, txa, va, sat_a = travar_em(a, sa, x)
    log(f"2) Ana travou {x} na rede A ({end_a[:20]}…), prazo bloco {t_a}")

    # Beto confere o contrato da Ana ANTES de travar o dele
    saida = a("gettxout", txa, va)
    assert saida and int(saida["value"] * 10**8) == sat_a, "contrato A não confere"
    t_b = b("getblockcount") + margem_b
    sb = htlc(h, ana_b.pub, beto_b.pub, t_b)
    end_b, txb, vb, sat_b = travar_em(b, sb, y)
    log(f"3) Beto conferiu e travou {y} na rede B ({end_b[:20]}…), prazo bloco {t_b}")

    resg_b = b("sendrawtransaction", gastar(sb, txb, vb, sat_b, b.destino(), ana_b.k, [s, b"\x01"]))
    b.minerar(1)
    log(f"4) Ana resgatou na rede B revelando S (tx {resg_b[:16]}…)")

    visto = bytes.fromhex(b("getrawtransaction", resg_b, True)["vin"][0]["txinwitness"][1])
    resg_a = a("sendrawtransaction", gastar(sa, txa, va, sat_a, a.destino(), beto_a.k, [visto, b"\x01"]))
    a.minerar(1)
    log(f"5) Beto leu S na rede B e resgatou na rede A (tx {resg_a[:16]}…)")
    return visto == s


def main():
    if "--ensaio" not in sys.argv:
        print(__doc__)
        return
    a = No(porta=29787, p2p=29777)
    b = No(porta=29797, p2p=29778)
    try:
        for n in (a, b):
            n("createwallet", "a")
            n.minerar(101)
        ok = trocar(a, b, "7", "2")
        print("\nTROCA COMPLETA ✔" if ok else "\nFALHOU")
        assert ok
    finally:
        a.parar(); b.parar()


if __name__ == "__main__":
    main()
