#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from gerar_header_snapshot import canonico, gerar  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "gerar_header_snapshot.py")


def snapshot(rede="principal", saidas=None, sha=None):
    d = {"rede": rede, "altura_antiga": 6000, "lancamento": "2026-12-01",
         "saidas": saidas or [{"script": "0014" + "11" * 20, "valor": 5, "tipo": "livre"}]}
    d["sha256"] = sha or hashlib.sha256(canonico(d)).hexdigest()
    return d


class TestGerador(unittest.TestCase):
    def rodar(self, dados, rede="principal"):
        with tempfile.TemporaryDirectory() as t:
            j = os.path.join(t, "s.json")
            out = os.path.join(t, "o.cpp")
            with open(j, "w") as fh:
                json.dump(dados, fh)
            r = subprocess.run([sys.executable, SCRIPT, f"--{rede}", j, "--saida", out], capture_output=True, text=True)
            return r, (open(out).read() if os.path.exists(out) else "")

    def test_tabela_gerada(self):
        r, cpp = self.rodar(snapshot())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('{"0014' + "11" * 20 + '", 5},', cpp)
        self.assertIn("std::vector<CTxOut> SnapshotTeste() { return {}; }", cpp)

    def test_sha_errado(self):
        r, _ = self.rodar(snapshot(sha="00" * 32))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sha256", r.stderr)

    def test_rede_errada(self):
        r, _ = self.rodar(snapshot(rede="teste"), rede="principal")
        self.assertNotEqual(r.returncode, 0)

    def test_valor_invalido(self):
        r, _ = self.rodar(snapshot(saidas=[{"script": "0014" + "11" * 20, "valor": 0}]))
        self.assertNotEqual(r.returncode, 0)

    def test_sem_snapshot(self):
        self.assertIn("SnapshotPrincipal() { return {}; }", gerar([], []))


if __name__ == "__main__":
    unittest.main()
