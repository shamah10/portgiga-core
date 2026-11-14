// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <clientversion.h>
#include <util/fs_helpers.h>

#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_SUITE(portgiga_nomes_tests)

BOOST_AUTO_TEST_CASE(pasta_de_dados_padrao)
{
    BOOST_CHECK_EQUAL(fs::PathToString(GetDefaultDataDir().filename()), ".portgiga");
}

BOOST_AUTO_TEST_CASE(nome_do_cliente)
{
    BOOST_CHECK(FormatSubVersion(UA_NAME, CLIENT_VERSION, {}).find("/Portgiga:") == 0);
}

BOOST_AUTO_TEST_SUITE_END()
