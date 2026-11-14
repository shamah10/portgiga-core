// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <kernel/portgiga_snapshot.h>

#include <script/script.h>
#include <util/strencodings.h>

namespace portgiga {

std::vector<CTxOut> SaidasDeTabela(const SaidaSnapshot* tabela, size_t tamanho)
{
    std::vector<CTxOut> saidas;
    saidas.reserve(tamanho);
    for (size_t i = 0; i < tamanho; ++i) {
        const auto bytes = ParseHex(tabela[i].script_hex);
        saidas.emplace_back(tabela[i].valor, CScript(bytes.begin(), bytes.end()));
    }
    return saidas;
}

static bool EhCompromissoSegwit(const CScript& s)
{
    return s.size() >= 38 && s[0] == OP_RETURN && s[1] == 0x24 && s[2] == 0xaa && s[3] == 0x21 && s[4] == 0xa9 && s[5] == 0xed;
}

bool CoinbaseConfereSnapshot(const CTransaction& coinbase, const std::vector<CTxOut>& snapshot)
{
    const auto& vout = coinbase.vout;
    if (vout.size() == snapshot.size() + 1) {
        if (!EhCompromissoSegwit(vout.back().scriptPubKey)) return false;
    } else if (vout.size() != snapshot.size()) {
        return false;
    }
    for (size_t i = 0; i < snapshot.size(); ++i) {
        if (vout[i] != snapshot[i]) return false;
    }
    return true;
}

} // namespace portgiga
