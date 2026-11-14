// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <common/args.h>
#include <pow.h>
#include <primitives/block.h>
#include <util/chaintype.h>

#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_SUITE(portgiga_pow_tests)

// Vetor gerado por contrib/portgiga/pow_ref.py: pow_hash(80 bytes zerados), mostrado como uint256 (invertido)
BOOST_AUTO_TEST_CASE(hash_pow_do_cabecalho_zerado)
{
    CBlockHeader h;
    h.SetNull();
    BOOST_CHECK_EQUAL(h.GetPoWHash().GetHex(), "de954af3ba8c07ae4be14b9b6be0ee54f1ad73eb834143c44a71062ff73c016f");
    BOOST_CHECK(h.GetPoWHash() != h.GetHash());
}

BOOST_AUTO_TEST_CASE(genesis_atende_o_pow_portgiga)
{
    for (ChainType t : {ChainType::MAIN, ChainType::TESTNET, ChainType::REGTEST}) {
        ArgsManager args;
        const auto p = CreateChainParams(args, t);
        const CBlock& g = p->GenesisBlock();
        BOOST_CHECK(CheckProofOfWork(g.GetPoWHash(), g.nBits, p->GetConsensus()));
    }
}

BOOST_AUTO_TEST_SUITE_END()
