#!/usr/bin/env python3
# Copyright (c) 2026 The Portgiga developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Referência da prova de trabalho da Portgiga (usada pelos testes, pelo pool e pelo firmware).

hash_pow = SHA256d(b"PTG\\x01" + cabeçalho de 80 bytes). O hash de identidade do bloco continua SHA256d(cabeçalho).
Os bytes saem na ordem do SHA-256 (como o Bitcoin guarda internamente); o número comparado com o alvo é
esse valor lido em little-endian.
"""
import hashlib
import struct

PREFIXO_POW = b"PTG\x01"


def sha256d(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def pow_hash(header80: bytes) -> bytes:
    if len(header80) != 80:
        raise ValueError("o cabeçalho tem 80 bytes")
    return sha256d(PREFIXO_POW + header80)


def alvo_de_nbits(nbits: int) -> int:
    expoente = nbits >> 24
    mantissa = nbits & 0x007FFFFF
    return mantissa << (8 * (expoente - 3)) if expoente > 3 else mantissa >> (8 * (3 - expoente))


def cabecalho(versao: int, anterior: bytes, merkle: bytes, tempo: int, nbits: int, nonce: int) -> bytes:
    return struct.pack("<i", versao) + anterior + merkle + struct.pack("<III", tempo, nbits, nonce)


def minerar_genesis(versao: int, merkle: bytes, tempo: int, nbits: int, nonce_inicial: int = 0) -> int:
    """Primeiro nonce cujo hash de PoW atende o alvo (anterior = zeros)."""
    alvo = alvo_de_nbits(nbits)
    base = struct.pack("<i", versao) + bytes(32) + merkle + struct.pack("<II", tempo, nbits)
    for nonce in range(nonce_inicial, 2**32):
        if int.from_bytes(pow_hash(base + struct.pack("<I", nonce)), "little") <= alvo:
            return nonce
    raise RuntimeError("nenhum nonce serve; troque o horário")


MENSAGEM_GENESIS = b"Portgiga 13/11/2026 - simbolo: o pau-brasil"


def _push(dados: bytes) -> bytes:
    assert len(dados) < 0x4c
    return bytes([len(dados)]) + dados


def coinbase_genesis(mensagem: bytes = MENSAGEM_GENESIS) -> bytes:
    """Transação do bloco gênese da Portgiga: mesma forma da do Bitcoin, saída OP_RETURN de valor zero."""
    script_sig = _push((486604799).to_bytes(4, "little")) + _push(b"\x04") + _push(mensagem)
    script_saida = b"\x6a"  # OP_RETURN: nunca pode ser gasta
    return (struct.pack("<i", 1) + b"\x01" + bytes(32) + b"\xff\xff\xff\xff" + bytes([len(script_sig)]) + script_sig
            + b"\xff\xff\xff\xff" + b"\x01" + struct.pack("<q", 0) + bytes([len(script_saida)]) + script_saida
            + struct.pack("<I", 0))


def gerar_genesis(tempo: int, nbits: int):
    """(merkle_hex_uint256, nonce, hash_hex_uint256) do gênese da Portgiga."""
    merkle = sha256d(coinbase_genesis())
    nonce = minerar_genesis(1, merkle, tempo, nbits)
    h = cabecalho(1, bytes(32), merkle, tempo, nbits, nonce)
    return merkle[::-1].hex(), nonce, sha256d(h)[::-1].hex()


if __name__ == "__main__":
    import sys
    tempo = int(sys.argv[1])
    for nome, nbits in (("principal", 0x1e0fffff), ("teste", 0x1e0fffff)):
        m, n, h = gerar_genesis(tempo if nome == "principal" else tempo + 1, nbits)
        print(nome, "tempo", tempo if nome == "principal" else tempo + 1, "nonce", n, "merkle", m, "hash", h)
