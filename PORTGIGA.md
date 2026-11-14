# Portgiga Core

Nó da rede Portgiga (PTG), derivado do Bitcoin Core v29.0 (commit f490f55, tag v29.0 clonada de
https://github.com/bitcoin/bitcoin). A assinatura da tag não foi conferida com GPG neste PC.

## O que mudou em relação ao Bitcoin Core

- Etapa 1: pasta de dados `~/.portgiga`; o nó se apresenta como `/Portgiga:29.0.0/`; nome do cliente "Portgiga Core".
  Os programas são `build/bin/portgigad`, `portgiga-cli`, `portgiga-wallet`, `portgiga-tx`, `portgiga-util`
  (atalhos para os executáveis internos, que mantêm os nomes do Bitcoin Core para não quebrar os testes).
  O arquivo de configuração continua se chamando `bitcoin.conf` (dentro de `~/.portgiga`).

## Dependências (Ubuntu)

Rode uma vez (pede a senha do PC):

    sudo apt install build-essential cmake pkgconf python3 libevent-dev libboost-dev libsqlite3-dev

## Compilar

    cmake -B build -DBUILD_GUI=OFF -DENABLE_IPC=OFF
    cmake --build build -j4
    ctest --test-dir build -j4
