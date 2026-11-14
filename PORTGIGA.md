# Portgiga Core

Nó da rede Portgiga (PTG), derivado do Bitcoin Core v29.0 (commit f490f55, tag v29.0 clonada de
https://github.com/bitcoin/bitcoin). A assinatura da tag não foi conferida com GPG neste PC.

## O que mudou em relação ao Bitcoin Core

- Etapa 1: pasta de dados `~/.portgiga`; o nó se apresenta como `/Portgiga:29.0.0/`; nome do cliente "Portgiga Core".
  Os programas são `build/bin/portgigad`, `portgiga-cli`, `portgiga-wallet`, `portgiga-tx`, `portgiga-util`
  (atalhos para os executáveis internos, que mantêm os nomes do Bitcoin Core para não quebrar os testes).
  O arquivo de configuração continua se chamando `bitcoin.conf` (dentro de `~/.portgiga`).
- Etapa 2: regras da rede. Principal e teste: bloco a cada 60 s, halving a cada 1.051.200 blocos, limite de
  21.024.000 PTG, soft forks (BIP34/65/66, CSV, SegWit, Taproot) ativos desde o bloco 1, endereços `ptg1…`
  (principal) e `tptg1…` (teste), portas P2P/RPC 9777/9778 (principal), 19777/19778 (teste), 29777/29778 (regtest),
  bytes mágicos d0 50 47 a1 / d1 50 47 a2 / d2 50 47 a3. Sem sementes de DNS, checkpoints ou assumeutxo.
  A regtest mantém as regras de teste do Bitcoin (halving a cada 150, endereços `bcrt1…`) para a suíte de
  testes original continuar servindo; testnet4 e signet do Bitcoin não são usadas pela Portgiga.
- Etapa 3: prova de trabalho própria. `CBlockHeader::GetPoWHash()` = SHA256d("PTG\x01" + cabeçalho de 80 bytes);
  o hash de identidade do bloco continua `GetHash()`. Referência em Python: `contrib/portgiga/pow_ref.py`.
  Dificuldade mínima (`powLimit`) da principal e da teste: `00000fff…` (~1 milhão de hashes por bloco), para poucas
  ESP32 conseguirem fechar blocos no começo. Gêneses novos (mensagem "Portgiga 13/11/2026 - simbolo: o pau-brasil",
  saída OP_RETURN de valor zero): principal 9c263318…d2b1, teste 6382c96c…29a6. A regtest manteve o gênese do
  Bitcoin, que já atende o hash novo.
- Etapa 4: dificuldade a cada bloco (LWMA-1, N = 60, T = 60 s; cada intervalo limitado a [1, 6T]) em
  `LwmaNextWork` (`src/pow.cpp`). As primeiras N+1 alturas usam a dificuldade mínima. A regra especial de
  dificuldade mínima da testnet foi desligada (a LWMA cobre períodos lentos). Na regtest nada muda.
- Etapa 5: emissão. 10 PTG por bloco (`nSubsidyBase`), halving a cada 1.051.200 blocos contando a altura da rede
  antiga (`nAlturaAntigaSnapshot`, definida no lançamento); o bloco 1 paga o total do snapshot (`nSnapshotTotal`).
  A regtest continua com 50 por bloco e halving a cada 150, como no Bitcoin.

## Dependências (Ubuntu)

Rode uma vez (pede a senha do PC):

    sudo apt install build-essential cmake pkgconf python3 libevent-dev libboost-dev libsqlite3-dev

## Compilar

    cmake -B build -DBUILD_GUI=OFF -DENABLE_IPC=OFF
    cmake --build build -j4
    ctest --test-dir build -j4

## Testes do Bitcoin Core que não valem para a Portgiga

Estes testes unitários conferem valores da rede do Bitcoin (endereços `1…`/`3…`/`bc1…`, chaves WIF com prefixo 128,
recompensas de 50 BTC, ajuste de dificuldade a cada 2.016 blocos, vetores do BIP324 com os bytes mágicos do Bitcoin,
limite de 21.000.000) e falham de propósito na Portgiga. A lista fica em `contrib/portgiga/ctest-excluidos.txt`:

    ctest --test-dir build -j4 -E "$(cat contrib/portgiga/ctest-excluidos.txt)"

`validation_chainstate_tests` e `validation_chainstatemanager_tests` usam os snapshots assumeutxo da regtest do Bitcoin (hashes de blocos mudaram com o PoW novo; a Portgiga não usa assumeutxo).

`pow_tests` (vetores do ajuste a cada 2.016 blocos do Bitcoin) e `validation_tests` (recompensa inicial de 50 BTC e soma de
subsídios em passos de 1.000 blocos, que não fecha com o intervalo de 1.051.200) seguem fora; a dificuldade e a emissão
da Portgiga têm testes próprios (`portgiga_lwma_tests`, `portgiga_subsidio_tests`).

### Testes funcionais do Bitcoin que não valem para a Portgiga

Lista em `contrib/portgiga/funcionais-excluidos.txt` (rodar com
`python3 build/test/functional/test_runner.py -j4 --exclude "$(cat contrib/portgiga/funcionais-excluidos.txt)"`):

- assumeutxo/dumptxoutset (`feature_assumeutxo`, `wallet_assumeutxo`, `rpc_dumptxoutset`): usam hashes de snapshots da
  regtest do Bitcoin; com o hash de PoW novo os blocos minerados mudam de nonce e de hash.
- `rpc_getblockfrompeer`, `rpc_getblockstats`: comparam com hashes/dados gravados de blocos do Bitcoin.
- `rpc_validateaddress`, `wallet_crosschain`, `mining_mainnet`, `p2p_dos_header_tree`: vetores e cabeçalhos das redes
  principal/testnet do Bitcoin.
- `feature_signet`, `tool_signet_miner`, `feature_config_args`: usam signet/testnet4 do Bitcoin, cujos gêneses não
  atendem o PoW da Portgiga (a Portgiga não usa essas redes).

Resultado da suíte completa depois da etapa 3: 321 testes, 13 falhas, todas acima; `feature_loadblock` foi corrigido
(bytes mágicos da regtest).
