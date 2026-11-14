#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Gera src/kernel/portgiga_snapshot_dados.cpp a partir dos snapshots (JSON da ferramenta de snapshot da rede antiga).

Uso: gerar_header_snapshot.py [--principal snapshot.json] [--teste snapshot.json] --saida src/kernel/portgiga_snapshot_dados.cpp
Sem arquivo para uma rede, a tabela dela fica vazia (sem snapshot).
Confere o campo sha256 de cada arquivo (JSON canônico sem esse campo: chaves em ordem, separadores compactos).
"""
import argparse
import hashlib
import json
import re
import sys

CABECALHO = """// Copyright (c) 2026 The Portgiga developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
//
// ARQUIVO GERADO por contrib/portgiga/gerar_header_snapshot.py. Não edite à mão.

#include <kernel/portgiga_snapshot.h>

namespace portgiga {
"""


def canonico(dados: dict) -> bytes:
    semhash = {k: v for k, v in dados.items() if k != "sha256"}
    return json.dumps(semhash, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def carregar(caminho: str, rede: str):
    """(saídas, altura_antiga) de um snapshot conferido."""
    with open(caminho, encoding="utf-8") as fh:
        dados = json.load(fh)
    if dados.get("rede") != rede:
        sys.exit(f"{caminho}: rede '{dados.get('rede')}', esperado '{rede}'")
    if hashlib.sha256(canonico(dados)).hexdigest() != dados.get("sha256"):
        sys.exit(f"{caminho}: sha256 não confere")
    saidas = []
    for i, s in enumerate(dados["saidas"]):
        if not re.fullmatch(r"(?:[0-9a-f]{2})+", s["script"]) or not isinstance(s["valor"], int) or s["valor"] <= 0:
            sys.exit(f"{caminho}: saída {i} inválida")
        saidas.append((s["script"], s["valor"]))
    altura = dados.get("altura_antiga")
    if not isinstance(altura, int) or altura <= 0:
        sys.exit(f"{caminho}: altura_antiga precisa ser a altura da rede antiga no snapshot (maior que zero)")
    return saidas, altura


def tabela(nome: str, funcao: str, dados) -> str:
    saidas, altura = dados
    fn_altura = f"int SnapshotAlturaAntiga{funcao[len('Snapshot'):]}() {{ return {altura}; }}\n"
    if not saidas:
        return f"\nstd::vector<CTxOut> {funcao}() {{ return {{}}; }}\n" + fn_altura
    linhas = "\n".join(f'    {{"{sc}", {v}}},' for sc, v in saidas)
    return (f"\nstatic const SaidaSnapshot {nome}[] = {{\n{linhas}\n}};\n"
            f"std::vector<CTxOut> {funcao}() {{ return SaidasDeTabela({nome}, sizeof({nome}) / sizeof({nome}[0])); }}\n" + fn_altura)


def gerar(principal, teste) -> str:
    return CABECALHO + tabela("SNAPSHOT_PRINCIPAL", "SnapshotPrincipal", principal) + tabela("SNAPSHOT_TESTE", "SnapshotTeste", teste) + "\n} // namespace portgiga\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--principal")
    ap.add_argument("--teste")
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    texto = gerar(carregar(a.principal, "principal") if a.principal else ([], 0), carregar(a.teste, "teste") if a.teste else ([], 0))
    with open(a.saida, "w", encoding="utf-8") as fh:
        fh.write(texto)


if __name__ == "__main__":
    main()
