"""
Authoritative CRC and checksum implementations for embedded protocols.
Used as deterministic ground truth in training examples, reward functions, and benchmarks.
"""

from typing import Union


def crc16_modbus(data: Union[bytes, bytearray]) -> int:
    """
    Calculate CRC-16 Modbus (IBM).
    Polynomial: 0x8005 (reversed: 0xA001)
    Initial Value: 0xFFFF
    Reflected In: True, Reflected Out: True, XOR Out: 0x0000
    Returns: 16-bit integer (low byte first on wire).
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def crc16_ccitt(data: Union[bytes, bytearray], init: int = 0xFFFF) -> int:
    """
    Calculate CRC-16 CCITT (XModem or standard).
    Polynomial: 0x1021
    """
    crc = init
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


def crc8_maxim(data: Union[bytes, bytearray]) -> int:
    """
    Calculate CRC-8 Dallas/Maxim (used in 1-Wire sensors like DS18B20).
    Polynomial: 0x31 (reflected: 0x8C)
    Initial Value: 0x00
    """
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc & 0xFF


def nmea_checksum(sentence: str) -> str:
    """
    Calculate NMEA-0183 XOR checksum.
    Payload is between '$' and '*'.
    Returns 2-digit uppercase hex string.
    """
    # Strip leading $ and trailing * if present
    clean = sentence.strip()
    if clean.startswith("$"):
        clean = clean[1:]
    if "*" in clean:
        clean = clean.split("*")[0]
    
    chk = 0
    for char in clean:
        chk ^= ord(char)
    return f"{chk:02X}"
