# Listagem da PTG em plataformas de troca P2P (Komodo / BasicSwap)

| Peça | Arquivo | Status |
|---|---|---|
| Ficha da moeda (formato KomodoPlatform/coins) | `komodo/PTG.json` | pronta (PTG + PTGT) |
| Servidores Electrum (formato do repo) | `komodo/electrums/PTG` | endereços provisórios: dependem do domínio |
| Explorador | `komodo/explorers/PTG` | provisório: depende do domínio |
| Ícone 128×128 | `komodo/ptg.png` | pronto |
| Classe ElectrumX 2.x | `electrumx/portgiga_coin.py` + lançador `electrumx_portgiga.py` | **testada** em regtest (`electrumx/teste_regtest.py`) |

ElectrumX instalado em `~/.local/share/portgiga/electrumx-venv` (e-x 2.0.1 + plyvel).
Teste: `~/.local/share/portgiga/electrumx-venv/bin/python electrumx/teste_regtest.py`

Falta (em ordem):
1. Rede nova no ar + domínio → 2 servidores ElectrumX públicos com SSL (portas 50701 tcp / 50702 ssl).
2. ~~MESSAGE_MAGIC~~ feito ("Portgiga Signed Message:\n"). Falta pedir número SLIP-44.
3. Testar uma troca com o binário do Komodo DeFi Framework (download precisa ser feito pelo dono).
4. Advogado → só então o pull request no KomodoPlatform/coins (a listagem exige uma troca real concluída).
