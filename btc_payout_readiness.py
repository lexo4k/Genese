"""Offline Bitcoin mainnet payout-destination validation for GÊNESE PAY.

This module validates a configured native SegWit v0 P2WPKH address only.
It does not connect to NiceHash, change provider payout settings, create revenue,
or send/withdraw funds.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_MAP = {char: index for index, char in enumerate(_BECH32_CHARSET)}
_GENERATORS = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)


def _polymod(values: list[int]) -> int:
    checksum = 1
    for value in values:
        top = checksum >> 25
        checksum = ((checksum & 0x1FFFFFF) << 5) ^ value
        for index, generator in enumerate(_GENERATORS):
            if (top >> index) & 1:
                checksum ^= generator
    return checksum


def _hrp_expand(hrp: str) -> list[int]:
    return [ord(char) >> 5 for char in hrp] + [0] + [ord(char) & 31 for char in hrp]


def _convert_bits(data: list[int], from_bits: int, to_bits: int, pad: bool) -> list[int] | None:
    accumulator = 0
    bit_count = 0
    result: list[int] = []
    max_value = (1 << to_bits) - 1
    max_accumulator = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        accumulator = ((accumulator << from_bits) | value) & max_accumulator
        bit_count += from_bits
        while bit_count >= to_bits:
            bit_count -= to_bits
            result.append((accumulator >> bit_count) & max_value)
    if pad:
        if bit_count:
            result.append((accumulator << (to_bits - bit_count)) & max_value)
    elif bit_count >= from_bits or ((accumulator << (to_bits - bit_count)) & max_value):
        return None
    return result


def validate_mainnet_p2wpkh(address: str) -> tuple[bool, str]:
    """Validate a mainnet bc1 native SegWit v0 20-byte witness program."""
    if not isinstance(address, str) or not address:
        return False, "endereco_ausente"
    if address.lower() != address and address.upper() != address:
        return False, "mistura_de_maiusculas_e_minusculas"
    value = address.lower()
    if len(value) > 90 or not value.startswith("bc1"):
        return False, "nao_e_endereco_bitcoin_mainnet_bc1"
    separator = value.rfind("1")
    if separator < 1 or separator + 7 > len(value):
        return False, "formato_bech32_invalido"
    hrp = value[:separator]
    if hrp != "bc":
        return False, "rede_nao_e_mainnet"
    try:
        data = [_BECH32_MAP[char] for char in value[separator + 1:]]
    except KeyError:
        return False, "caractere_bech32_invalido"
    if _polymod(_hrp_expand(hrp) + data) != 1:
        return False, "checksum_bech32_invalido"
    payload = data[:-6]
    if not payload or payload[0] != 0:
        return False, "versao_witness_nao_suportada"
    program = _convert_bits(payload[1:], 5, 8, False)
    if program is None or len(program) != 20:
        return False, "programa_witness_nao_e_p2wpkh"
    return True, "endereco_bitcoin_mainnet_p2wpkh_valido"


def build_report(address: str | None = None) -> dict[str, Any]:
    destination = (address if address is not None else os.environ.get("GENESE_BTC_PAYOUT_ADDRESS", "")).strip()
    valid, reason = validate_mainnet_p2wpkh(destination)
    return {
        "produto": "GENESE PAY",
        "provider": "NiceHash",
        "destination_type": "Bitcoin mainnet native SegWit v0 P2WPKH",
        "destination_configured": bool(destination),
        "destination_valid": valid,
        "destination": destination if valid else None,
        "validation": reason,
        "payout_api_enabled": False,
        "withdrawal_executed": False,
        "revenue_confirmed": False,
        "limitations": [
            "Validar o endereço não confirma que ele pertence ao usuário.",
            "Este módulo não altera o endereço de pagamento na NiceHash.",
            "Este módulo não solicita nem executa saques.",
            "A NiceHash precisa ter fundos disponíveis e aceitar o endereço/rede.",
            "Nunca use este relatório como prova de pagamento ou depósito na carteira.",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["destination_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
