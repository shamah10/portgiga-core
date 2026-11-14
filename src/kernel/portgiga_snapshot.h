// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_KERNEL_PORTGIGA_SNAPSHOT_H
#define BITCOIN_KERNEL_PORTGIGA_SNAPSHOT_H

#include <primitives/transaction.h>

#include <cstdint>
#include <vector>

namespace portgiga {

//! Uma saída do snapshot: scriptPubKey em hexadecimal e valor em unidades (1 PTG = 100.000.000)
struct SaidaSnapshot {
    const char* script_hex;
    int64_t valor;
};

//! Snapshot da rede principal / de teste (tabelas geradas por contrib/portgiga/gerar_header_snapshot.py)
std::vector<CTxOut> SnapshotPrincipal();
std::vector<CTxOut> SnapshotTeste();

//! Converte uma tabela gerada em saídas
std::vector<CTxOut> SaidasDeTabela(const SaidaSnapshot* tabela, size_t tamanho);

//! O coinbase do bloco 1 confere com o snapshot? Aceita, depois da lista, só o compromisso SegWit (OP_RETURN aa21a9ed).
bool CoinbaseConfereSnapshot(const CTransaction& coinbase, const std::vector<CTxOut>& snapshot);

} // namespace portgiga

#endif // BITCOIN_KERNEL_PORTGIGA_SNAPSHOT_H
