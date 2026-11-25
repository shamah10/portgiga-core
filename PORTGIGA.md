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
  (principal) e `tptg1…` (teste), portas P2P/RPC 9777/9787 (principal), 19777/19787 (teste), 29777/29787 (regtest); a porta P2P+1 fica para o Tor,
  bytes mágicos d0 50 47 a1 / d1 50 47 a2 / d2 50 47 a3. Sem sementes de DNS, checkpoints ou assumeutxo.
  A regtest mantém as regras de teste do Bitcoin (halving a cada 150, endereços `bcrt1…`) para a suíte de
  testes original continuar servindo; testnet4 e signet do Bitcoin não são usadas pela Portgiga.
- Etapa 3: prova de trabalho própria. `CBlockHeader::GetPoWHash()` = SHA256d("PTG\x01" + cabeçalho de 80 bytes);
  o hash de identidade do bloco continua `GetHash()`. Referência em Python: `contrib/portgiga/pow_ref.py`.
  Dificuldade mínima (`powLimit`) da principal e da teste: `00000fff…` (~1 milhão de hashes por bloco), para poucas
  ESP32 conseguirem fechar blocos no começo. Gêneses novos (mensagem "Portgiga 13/11/2026 - simbolo: o pau-brasil",
  saída OP_RETURN de valor zero): principal 9c263318…d2b1, teste 6382c96c…29a6. A regtest manteve o gênese do
  Bitcoin, que já atende o hash novo.
- Etapa 4: dificuldade a cada bloco (LWMA-1, N = 60, T = 60 s; horários monotônicos e cada intervalo limitado a 6T) em
  `LwmaNextWork` (`src/pow.cpp`). As primeiras N+1 alturas usam a dificuldade mínima. A regra especial de
  dificuldade mínima da testnet foi desligada (a LWMA cobre períodos lentos). Na regtest nada muda.
- Etapa 5: emissão. 10 PTG por bloco (`nSubsidyBase`), halving a cada 1.051.200 blocos contando a altura da rede
  antiga (`nAlturaAntigaSnapshot`, definida no lançamento); o bloco 1 paga o total do snapshot (`nSnapshotTotal`).
  A regtest continua com 50 por bloco e halving a cada 150, como no Bitcoin.
- Etapa 6: snapshot no bloco 1. O coinbase do bloco 1 tem que ser exatamente a lista do snapshot (mais o compromisso
  SegWit); senão o bloco é recusado com `bad-portgiga-snapshot`. O minerador monta esse coinbase sozinho. As tabelas da
  principal e da teste ficam em `src/kernel/portgiga_snapshot_dados.cpp`, geradas por
  `contrib/portgiga/gerar_header_snapshot.py` a partir do JSON da ferramenta de snapshot (vazias até o lançamento), junto
  com a altura da rede antiga (`SnapshotAlturaAntiga…`); o nó para na partida se houver snapshot sem altura ou vice-versa.
  Mineração do bloco 1 no lançamento: pelo próprio nó (`generatetoaddress`/`generateblock`), não por pool.
  Parcelas travadas: P2WSH de `wsh(and_v(v:pk(DONO),after(DATA)))`, gastas com a carteira importando esse descritor
  e uma transação com `nLockTime` = DATA. Na regtest, `-snapshotteste=<arquivo.json>` carrega um snapshot de teste.

- Etapa 7: identidade própria para carteiras e listagem. Mensagens assinadas usam o prefixo
  "Portgiga Signed Message:\n" (`MESSAGE_MAGIC` em `src/common/signmessage.cpp`): uma assinatura do Bitcoin não vale
  na Portgiga e vice-versa. A carteira da rede principal deriva no coin type SLIP-0044 **7770**
  (`m/44'|49'|84'|86'/7770'/0'`, `src/wallet/walletutil.cpp`); teste e regtest seguem em 1'. Os testes de mensagem de
  `util_tests` foram reescritos com endereços `P…`/`p…` da Portgiga, e `util_tests` saiu da lista de excluídos.

## Rodar um nó da Portgiga

Qualquer pessoa pode rodar um nó: ele guarda a corrente inteira, confere cada bloco sozinho e ajuda a rede a não depender
de ninguém. Num Ubuntu:

1. Instale as dependências e compile (seções abaixo).
2. Ligue o nó em segundo plano:

       build/bin/portgigad -daemon

3. Veja se está funcionando:

       build/bin/portgiga-cli getblockchaininfo

4. Conecte a outro nó da rede (endereço de quem já roda um; os fixos entram no código no lançamento):

       build/bin/portgiga-cli addnode "IP-DO-OUTRO-NO:9777" add

5. Para desligar:

       build/bin/portgiga-cli stop

Os dados ficam em `~/.portgiga`. Para quem só quer testar sem mexer na rede de verdade, use `-chain=test`
(ou `-regtest` para uma rede só sua) em todos os comandos.

Para deixar o nó ligado 24 h e aceitando conexões de outros nós, crie `~/.portgiga/bitcoin.conf` com:

    server=1
    listen=1
    txindex=1
    maxtipage=315360000

e abra a porta **9777** no roteador (redirecionar para o IP do PC). O `maxtipage` longo evita que um nó que ficou
desligado por dias fique preso em "sincronizando" numa rede pequena. Quem quiser minerar precisa também do pool
(repositório `portgiga-pool`), porque um nó sozinho e sem conexões não entrega trabalho para mineradores.

## Seeds (nós fixos no código)

Um nó novo precisa achar os outros. No começo, isso é feito à mão com `addnode` (acima). Quando houver um nó com
**IP fixo que aceite conexões na porta 9777** (o do dono ou o de qualquer voluntário), ele entra no código:

- `src/kernel/chainparams.cpp`, na rede principal: `vFixedSeeds` (lista de IPs fixos, gerada por
  `contrib/seeds/generate-seeds.py` a partir de um arquivo `nodes_main.txt` com `IP:9777` por linha) e, se um dia houver
  domínio com DNS de descoberta, `vSeeds.emplace_back("seed.exemplo.com.br")`.
- Recompile e publique a versão nova. Nós antigos continuam funcionando; os novos acham a rede sozinhos.

Nenhum IP é inventado aqui: a lista fica vazia até existir um endereço que aceite conexões de verdade (conferir de um
celular no 4G antes de pôr no código). Mais de um seed, em lugares diferentes, é o que tira a rede da dependência de uma
pessoa.

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
