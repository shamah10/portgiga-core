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

`pow_tests` e `validation_tests` voltam a ser conferidos depois das etapas de dificuldade e emissão.
