// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <chainparamsbase.h>
#include <common/args.h>
#include <consensus/amount.h>
#include <util/chaintype.h>

#include <boost/test/unit_test.hpp>

#include <array>

BOOST_AUTO_TEST_SUITE(portgiga_params_tests)

static std::unique_ptr<const CChainParams> Rede(ChainType t)
{
    ArgsManager args;
    return CreateChainParams(args, t);
}

BOOST_AUTO_TEST_CASE(regras_da_rede_principal)
{
    const auto p = Rede(ChainType::MAIN);
    const auto& c = p->GetConsensus();
    BOOST_CHECK_EQUAL(c.nPowTargetSpacing, 60);
    BOOST_CHECK_EQUAL(c.nSubsidyHalvingInterval, 1051200);
    BOOST_CHECK_EQUAL(MAX_MONEY, CAmount{21'024'000} * COIN);
    BOOST_CHECK_EQUAL(p->Bech32HRP(), "ptg");
    BOOST_CHECK_EQUAL(p->GetDefaultPort(), 9777);
    BOOST_CHECK_EQUAL(CreateBaseChainParams(ChainType::MAIN)->RPCPort(), 9787);
    // soft forks ativos desde o começo
    BOOST_CHECK_EQUAL(c.BIP34Height, 1);
    BOOST_CHECK_EQUAL(c.SegwitHeight, 1);
    BOOST_CHECK(p->DNSSeeds().empty());
}

BOOST_AUTO_TEST_CASE(regras_da_rede_de_teste)
{
    const auto p = Rede(ChainType::TESTNET);
    BOOST_CHECK_EQUAL(p->GetConsensus().nPowTargetSpacing, 60);
    BOOST_CHECK_EQUAL(p->GetConsensus().nSubsidyHalvingInterval, 1051200);
    BOOST_CHECK_EQUAL(p->Bech32HRP(), "tptg");
    BOOST_CHECK_EQUAL(p->GetDefaultPort(), 19777);
    BOOST_CHECK_EQUAL(CreateBaseChainParams(ChainType::TESTNET)->RPCPort(), 19787);
}

BOOST_AUTO_TEST_CASE(regtest_portas)
{
    BOOST_CHECK_EQUAL(Rede(ChainType::REGTEST)->GetDefaultPort(), 29777);
    BOOST_CHECK_EQUAL(CreateBaseChainParams(ChainType::REGTEST)->RPCPort(), 29787);
}

BOOST_AUTO_TEST_CASE(porta_rpc_nao_colide_com_a_do_tor)
{
    // o nó escuta conexões do Tor na porta P2P + 1: o RPC não pode usar essa
    for (ChainType t : {ChainType::MAIN, ChainType::TESTNET, ChainType::REGTEST}) {
        BOOST_CHECK(CreateBaseChainParams(t)->RPCPort() != Rede(t)->GetDefaultPort() + 1);
    }
}

BOOST_AUTO_TEST_CASE(bytes_magicos_diferentes_do_bitcoin)
{
    const std::array<std::array<uint8_t, 4>, 3> bitcoin{{{0xf9, 0xbe, 0xb4, 0xd9}, {0x0b, 0x11, 0x09, 0x07}, {0xfa, 0xbf, 0xb5, 0xda}}};
    for (ChainType t : {ChainType::MAIN, ChainType::TESTNET, ChainType::REGTEST}) {
        const auto m = Rede(t)->MessageStart();
        for (const auto& b : bitcoin) {
            BOOST_CHECK(!std::equal(m.begin(), m.end(), b.begin()));
        }
    }
}

BOOST_AUTO_TEST_SUITE_END()
