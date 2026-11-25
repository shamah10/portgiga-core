# Pedido SLIP-0044 — Portgiga (PTG), coin type 7770

Linha a adicionar em slip-0044.md, mantendo a ordem (entre as linhas vizinhas):
| 7770       | PTG     | Portgiga                          |

Commit: `slip-0044: add Portgiga (PTG)`

Descrição do PR (inglês, como o repositório pede):
---
Registers coin type 7770 for Portgiga (PTG).

BIP-0044 wallet implementation: Portgiga Core (a Bitcoin Core v29 fork) derives mainnet
wallets at m/{44,49,84,86}'/7770'/0' — see src/wallet/walletutil.cpp:
<LINK PÚBLICO DO portgiga-core AQUI>
Project: https://github.com/shamah10/portgiga · https://portgiga.pages.dev
---

ABERTO em 25/11/2026: https://github.com/satoshilabs/slips/pull/2109
