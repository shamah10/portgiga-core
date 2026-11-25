#!/usr/bin/env python3
"""Teste ponta a ponta: portgigad -regtest + ElectrumX (classe Portgiga) + cliente Electrum.

Confere, pelo protocolo Electrum (o mesmo que carteiras e a Komodo usam):
  server.version · cabeçalho do topo bate com o nó · saldo de um endereço ·
  histórico · envio de transação (blockchain.transaction.broadcast) e o saldo novo.
Uso: ~/.local/share/portgiga/electrumx-venv/bin/python teste_regtest.py
"""
import hashlib, json, os, shutil, socket, subprocess, sys, tempfile, time
from decimal import Decimal

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "troca-atomica"))
from troca_regtest import No  # noqa: E402

PORTA_TCP = 50799


class Cliente:
    def __init__(self, porta):
        self.s = socket.create_connection(("127.0.0.1", porta), timeout=20)
        self.f = self.s.makefile("rb")
        self.n = 0

    def __call__(self, metodo, *params):
        self.n += 1
        self.s.sendall((json.dumps({"jsonrpc": "2.0", "id": self.n, "method": metodo,
                                    "params": list(params)}) + "\n").encode())
        while True:
            r = json.loads(self.f.readline())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(f"{metodo}: {r['error']}")
                return r["result"]


def scripthash(no, endereco):
    spk = bytes.fromhex(no("getaddressinfo", endereco, carteira="a")["scriptPubKey"])
    return hashlib.sha256(spk).digest()[::-1].hex()


def esperar_altura(cli, altura, limite=60):
    for _ in range(limite * 2):
        if cli("blockchain.headers.subscribe")["height"] >= altura:
            return
        time.sleep(0.5)
    raise SystemExit("ElectrumX não alcançou o nó")


def main():
    no = No()
    ex = None
    dbdir = tempfile.mkdtemp(prefix="ptg-electrumx-")
    try:
        no("createwallet", "a")
        meu = no("getnewaddress", carteira="a")
        no("generatetoaddress", 101, meu)
        genese = no("getblockhash", 0)
        env = dict(os.environ, COIN="Portgiga", NET="regtest", DB_ENGINE="leveldb",
                   DB_DIRECTORY=dbdir, DAEMON_URL="http://t:t@127.0.0.1:29787/",
                   SERVICES=f"tcp://127.0.0.1:{PORTA_TCP}", PTG_GENESIS=genese,
                   LOG_LEVEL="warning", ALLOW_ROOT="1")
        log = open(os.path.join(dbdir, "electrumx.log"), "w")
        ex = subprocess.Popen([sys.executable, os.path.join(AQUI, "electrumx_portgiga.py")],
                              env=env, stdout=log, stderr=subprocess.STDOUT)
        cli = None
        for _ in range(60):
            try:
                cli = Cliente(PORTA_TCP)
                break
            except OSError:
                if ex.poll() is not None:
                    log.flush()
                    print(open(log.name).read()[-3000:])
                    raise SystemExit("ElectrumX caiu")
                time.sleep(0.5)
        assert cli, "ElectrumX não abriu a porta"

        print("server.version:", cli("server.version", "teste-ptg", "1.4"))
        esperar_altura(cli, 101)
        topo = cli("blockchain.headers.subscribe")
        cab = bytes.fromhex(topo["hex"])
        hash_cab = hashlib.sha256(hashlib.sha256(cab).digest()).digest()[::-1].hex()
        assert hash_cab == no("getblockhash", topo["height"]), "cabeçalho não bate com o nó"
        print(f"topo {topo['height']}: cabeçalho confere com o nó ✔")

        sh = scripthash(no, meu)
        saldo = cli("blockchain.scripthash.get_balance", sh)
        print(f"saldo de {meu[:16]}… pelo Electrum: {saldo['confirmed'] / 1e8} (101 recompensas, 1 madura)")
        assert saldo["confirmed"] > 0
        hist = cli("blockchain.scripthash.get_history", sh)
        assert len(hist) == 101, len(hist)
        print(f"histórico: {len(hist)} transações ✔")

        # envio pela rede do Electrum
        destino = no("getnewaddress", carteira="a")
        bruto = no("createrawtransaction", [], {destino: "1.5"})
        bruto = no("fundrawtransaction", bruto, carteira="a")["hex"]
        assinado = no("signrawtransactionwithwallet", bruto, carteira="a")["hex"]
        txid = cli("blockchain.transaction.broadcast", assinado)
        assert txid == no("decoderawtransaction", assinado)["txid"]
        no("generatetoaddress", 1, meu)
        esperar_altura(cli, 102)
        sd = scripthash(no, destino)
        for _ in range(20):
            s2 = cli("blockchain.scripthash.get_balance", sd)
            if s2["confirmed"]:
                break
            time.sleep(0.5)
        assert s2["confirmed"] == 150_000_000, s2
        print(f"transação enviada pelo Electrum ({txid[:16]}…) confirmada; destino tem 1.5 PTG ✔")
        print("\nTUDO CERTO: o ElectrumX funciona com a Portgiga Core (regtest).")
    finally:
        if ex:
            ex.terminate()
            try:
                ex.wait(15)
            except subprocess.TimeoutExpired:
                ex.kill()
        no.parar()
        shutil.rmtree(dbdir, ignore_errors=True)


if __name__ == "__main__":
    main()
