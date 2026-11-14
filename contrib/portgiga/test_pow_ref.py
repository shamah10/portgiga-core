#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from pow_ref import pow_hash, sha256d, alvo_de_nbits, minerar_genesis  # noqa: E402


class TestPowRef(unittest.TestCase):
    def test_prefixo(self):
        h = bytes(80)
        self.assertEqual(pow_hash(h), hashlib.sha256(hashlib.sha256(b"PTG\x01" + h).digest()).digest())
        self.assertNotEqual(pow_hash(h), sha256d(h))

    def test_vetor_fixo(self):
        # mesmo vetor usado em src/test/portgiga_pow_tests.cpp
        self.assertEqual(pow_hash(bytes(80)).hex(), sha256d(b"PTG\x01" + bytes(80)).hex())

    def test_alvo(self):
        self.assertEqual(alvo_de_nbits(0x1d00ffff), 0xffff << (8 * 26))
        self.assertEqual(alvo_de_nbits(0x207fffff), 0x7fffff << (8 * 29))

    def test_minerar_facil(self):
        n = minerar_genesis(1, bytes(32), 1700000000, 0x207fffff)
        self.assertLess(n, 1000)

    def test_tamanho(self):
        with self.assertRaises(ValueError):
            pow_hash(bytes(79))


if __name__ == "__main__":
    unittest.main()
