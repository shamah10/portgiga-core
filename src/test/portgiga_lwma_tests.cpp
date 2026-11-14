// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <arith_uint256.h>
#include <chain.h>
#include <chainparams.h>
#include <common/args.h>
#include <pow.h>
#include <util/chaintype.h>

#include <boost/test/unit_test.hpp>

#include <deque>

BOOST_AUTO_TEST_SUITE(portgiga_lwma_tests)

namespace {
//! Cadeia de teste: cada bloco novo recebe o nBits que a LWMA pede (como um nó honesto faria)
struct Cadeia {
    const Consensus::Params& c;
    std::deque<CBlockIndex> blocos;
    explicit Cadeia(const Consensus::Params& p, uint32_t nbits_inicial) : c{p}
    {
        CBlockIndex& g = blocos.emplace_back();
        g.nHeight = 0;
        g.nTime = 1'800'000'000;
        g.nBits = nbits_inicial;
    }
    const CBlockIndex& topo() const { return blocos.back(); }
    uint32_t proximo_nbits() const
    {
        CBlockHeader h;
        h.nTime = topo().nTime + 60;
        return GetNextWorkRequired(&topo(), &h, c);
    }
    //! Acrescenta um bloco depois de `intervalo` segundos; `forcar_nbits` ignora a LWMA (montar a janela inicial)
    void adiciona(int64_t intervalo, std::optional<uint32_t> forcar_nbits = std::nullopt)
    {
        const uint32_t nbits = forcar_nbits ? *forcar_nbits : proximo_nbits();
        CBlockIndex& b = blocos.emplace_back();
        b.pprev = &blocos[blocos.size() - 2];
        b.nHeight = b.pprev->nHeight + 1;
        b.nTime = b.pprev->nTime + intervalo;
        b.nBits = nbits;
        b.BuildSkip();
    }
};

const Consensus::Params& Principal()
{
    static ArgsManager args;
    static const auto p = CreateChainParams(args, ChainType::MAIN);
    return p->GetConsensus();
}

arith_uint256 Alvo(uint32_t nbits)
{
    arith_uint256 a;
    a.SetCompact(nbits);
    return a;
}

uint32_t Compacto(const arith_uint256& a) { return a.GetCompact(); }

double Razao(const arith_uint256& a, const arith_uint256& b) { return a.getdouble() / b.getdouble(); }
} // namespace

BOOST_AUTO_TEST_CASE(comeco_da_rede_usa_o_limite)
{
    const auto& c = Principal();
    BOOST_CHECK_EQUAL(c.nLwmaN, 60);
    Cadeia k{c, Compacto(UintToArith256(c.powLimit) / 1000)};
    for (int i = 0; i < c.nLwmaN; ++i) k.adiciona(60, k.topo().nBits);
    // próximo bloco tem altura N+1: ainda é o limite
    BOOST_CHECK_EQUAL(k.proximo_nbits(), UintToArith256(c.powLimit).GetCompact());
}

BOOST_AUTO_TEST_CASE(blocos_a_cada_minuto_mantem_o_alvo)
{
    const auto& c = Principal();
    const uint32_t base = Compacto(UintToArith256(c.powLimit) / 1000);
    Cadeia k{c, base};
    for (int i = 0; i < c.nLwmaN + 2; ++i) k.adiciona(60, base);
    for (int i = 0; i < 200; ++i) k.adiciona(60);
    BOOST_CHECK_CLOSE(Razao(Alvo(k.topo().nBits), Alvo(base)), 1.0, 1.0);
}

BOOST_AUTO_TEST_CASE(dez_vezes_mais_poder_baixa_o_alvo)
{
    const auto& c = Principal();
    const uint32_t base = Compacto(UintToArith256(c.powLimit) / 1000);
    Cadeia k{c, base};
    for (int i = 0; i < c.nLwmaN + 2; ++i) k.adiciona(60, base);
    // com 10x mais poder, o intervalo esperado é 6 s × (alvo base / alvo atual)
    for (int i = 0; i < 400; ++i) {
        const double r = Razao(Alvo(k.proximo_nbits()), Alvo(base));
        k.adiciona(std::max<int64_t>(1, std::llround(6.0 / r)));
    }
    const double r = Razao(Alvo(k.topo().nBits), Alvo(base));
    BOOST_CHECK_MESSAGE(r > 0.07 && r < 0.14, "razão " << r);
}

BOOST_AUTO_TEST_CASE(dez_vezes_menos_poder_sobe_o_alvo_sem_passar_do_limite)
{
    const auto& c = Principal();
    const arith_uint256 limite = UintToArith256(c.powLimit);
    const uint32_t base = Compacto(limite / 100);
    Cadeia k{c, base};
    for (int i = 0; i < c.nLwmaN + 2; ++i) k.adiciona(60, base);
    for (int i = 0; i < 400; ++i) {
        const double r = Razao(Alvo(k.proximo_nbits()), Alvo(base));
        k.adiciona(std::max<int64_t>(1, std::llround(600.0 / r)));
        BOOST_CHECK(Alvo(k.topo().nBits) <= limite);
    }
    const double r = Razao(Alvo(k.topo().nBits), Alvo(base));
    BOOST_CHECK_MESSAGE(r > 7.0 && r < 14.0, "razão " << r);
}

BOOST_AUTO_TEST_CASE(horario_no_passado_nao_derruba_a_dificuldade)
{
    const auto& c = Principal();
    const uint32_t base = Compacto(UintToArith256(c.powLimit) / 1000);
    Cadeia k{c, base};
    for (int i = 0; i < c.nLwmaN + 2; ++i) k.adiciona(60, base);
    for (int i = 0; i < 30; ++i) k.adiciona(60);
    k.adiciona(-7200); // um minerador com o relógio 2 h atrasado
    k.adiciona(7260);  // o próximo volta ao horário certo
    const double r = Razao(Alvo(k.proximo_nbits()), Alvo(base));
    // o intervalo grande é limitado a 6×T, então o alvo sobe pouco
    BOOST_CHECK_MESSAGE(r < 1.20, "razão " << r);
}

BOOST_AUTO_TEST_CASE(transicao_permitida_em_qualquer_bloco)
{
    const auto& c = Principal();
    const uint32_t a = Compacto(UintToArith256(c.powLimit) / 1000);
    const uint32_t b = Compacto(UintToArith256(c.powLimit) / 900);
    BOOST_CHECK(PermittedDifficultyTransition(c, 12345, a, b));
}

BOOST_AUTO_TEST_SUITE_END()
