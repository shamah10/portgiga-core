"""Classes da Portgiga para o ElectrumX 2.x (servidor Electrum).

Uso: rodar com o lançador `electrumx_portgiga.py` (importa estas classes e inicia o
servidor), com COIN=Portgiga NET=mainnet|testnet|regtest DAEMON_URL=http://u:s@127.0.0.1:9787/
O nó precisa de -txindex=1.

O hash do bloco é o SHA256d padrão do cabeçalho (a prova de trabalho usa
SHA256d("PTG\\x01"+cabeçalho), mas o ElectrumX só encadeia cabeçalhos pelo hash
normal). Transações = formato SegWit do Bitcoin.

Herda de Coin (como Litecoin), não de Bitcoin: a classe Bitcoin do ElectrumX 2.x exige
Bitcoin Core >= 31 com txospenderindex, e o portgiga-core é baseado no v29.
"""
from electrumx.lib import tx as lib_tx
from electrumx.lib.coins import Coin


class Portgiga(Coin):
    NAME = "Portgiga"
    SHORTNAME = "PTG"
    NET = "mainnet"
    DESERIALIZER = lib_tx.DeserializerSegWit
    P2PKH_VERBYTE = bytes.fromhex("38")     # 56
    P2SH_VERBYTES = (bytes.fromhex("75"),)  # 117
    WIF_BYTE = bytes.fromhex("b8")          # 184
    GENESIS_HASH = ("9c263318bf10cf437221c73a86068f93"
                    "a202afaad118e2a032ee7e3ba415d2b1")
    RPC_PORT = 9787
    TX_COUNT = 1
    TX_COUNT_HEIGHT = 1
    TX_PER_BLOCK = 2
    REORG_LIMIT = 200
    PEERS = []          # preencher com os 2+ servidores públicos
    PEER_DEFAULT_PORTS = {'t': '50701', 's': '50702'}


class PortgigaTestnet(Portgiga):
    NET = "testnet"
    SHORTNAME = "PTGT"
    P2PKH_VERBYTE = bytes.fromhex("6f")
    P2SH_VERBYTES = (bytes.fromhex("c4"),)
    WIF_BYTE = bytes.fromhex("ef")
    GENESIS_HASH = ("6382c96cfeb47db1d4ca2fccba444374"
                    "ece10e16b426620a6a87e9cc7ab929a6")
    RPC_PORT = 19787
    PEER_DEFAULT_PORTS = {'t': '51701', 's': '51702'}


class PortgigaRegtest(PortgigaTestnet):
    NET = "regtest"
    SHORTNAME = "PTGR"
    GENESIS_HASH = None   # preenchido pelo teste a partir do nó (getblockhash 0)
    RPC_PORT = 29787


# O ElectrumX só procura moedas dentro do módulo electrumx.lib.coins: registra lá.
import electrumx.lib.coins as _coins  # noqa: E402
for _c in (Portgiga, PortgigaTestnet, PortgigaRegtest):
    setattr(_coins, _c.__name__, _c)
