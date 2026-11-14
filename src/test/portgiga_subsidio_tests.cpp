// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <common/args.h>
#include <consensus/amount.h>
#include <util/chaintype.h>
#include <validation.h>

#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_SUITE(portgiga_subsidio_tests)

static Consensus::Params Principal(int altura_antiga, CAmount snapshot)
{
    ArgsManager args;
    Consensus::Params c = CreateChainParams(args, ChainType::MAIN)->GetConsensus();
    c.nAlturaAntigaSnapshot = altura_antiga;
    c.nSnapshotTotal = snapshot;
    return c;
}

BOOST_AUTO_TEST_CASE(dez_ptg_por_bloco_e_metade_no_calendario_antigo)
{
    const auto c = Principal(6000, 0);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(2, c), 10 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(1051200 - 6000 - 1, c), 10 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(1051200 - 6000, c), 5 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(2 * 1051200 - 6000, c), 5 * COIN / 2);
}

BOOST_AUTO_TEST_CASE(bloco_um_paga_o_snapshot)
{
    BOOST_CHECK_EQUAL(GetBlockSubsidy(1, Principal(6000, 54250 * COIN)), 54250 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(1, Principal(0, 0)), 10 * COIN);
}

BOOST_AUTO_TEST_CASE(soma_nunca_passa_do_limite)
{
    const auto c = Principal(6000, 6000 * 10 * COIN);
    CAmount soma = c.nSnapshotTotal;
    for (int h = 2; h < 64 * 1051200; ++h) {
        const CAmount s = GetBlockSubsidy(h, c);
        if (s == 0) break;
        soma += s;
    }
    BOOST_CHECK(soma <= MAX_MONEY);
    BOOST_CHECK(MoneyRange(soma));
}

BOOST_AUTO_TEST_SUITE_END()
