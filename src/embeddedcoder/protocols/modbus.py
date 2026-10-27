"""
Modbus RTU and TCP protocol engine and frame validator.
"""

import struct
from typing import Dict, Any, Tuple, Optional
from embeddedcoder.protocols.crc import crc16_modbus


class ModbusRTU:
    @staticmethod
    def build_read_holding_registers(slave_id: int, start_address: int, quantity: int) -> bytes:
        """Build Function Code 0x03 frame: [SlaveID, 0x03, StartHi, StartLo, QtyHi, QtyLo, CRCLo, CRCHi]."""
        payload = struct.pack(">BBHH", slave_id, 0x03, start_address, quantity)
        crc = crc16_modbus(payload)
        return payload + struct.pack("<H", crc)

    @staticmethod
    def build_write_single_register(slave_id: int, address: int, value: int) -> bytes:
        """Build Function Code 0x06 frame: [SlaveID, 0x06, AddrHi, AddrLo, ValHi, ValLo, CRCLo, CRCHi]."""
        payload = struct.pack(">BBHH", slave_id, 0x06, address, value)
        crc = crc16_modbus(payload)
        return payload + struct.pack("<H", crc)

    @staticmethod
    def parse_frame(frame: bytes) -> Dict[str, Any]:
        """
        Parse and validate an arbitrary Modbus RTU frame.
        Checks minimum length, verifies CRC-16, and extracts PDU.
        """
        if len(frame) < 4:
            return {"valid": False, "error": "Frame too short (minimum 4 bytes required)"}

        payload = frame[:-2]
        received_crc = struct.unpack("<H", frame[-2:])[0]
        expected_crc = crc16_modbus(payload)

        if received_crc != expected_crc:
            return {
                "valid": False,
                "error": f"CRC mismatch: expected 0x{expected_crc:04X}, received 0x{received_crc:04X}",
                "slave_id": frame[0],
                "function_code": frame[1]
            }

        slave_id = frame[0]
        function_code = frame[1]

        # Check for exception response (bit 7 set)
        if function_code & 0x80:
            return {
                "valid": True,
                "is_exception": True,
                "slave_id": slave_id,
                "function_code": function_code & 0x7F,
                "exception_code": frame[2]
            }

        result: Dict[str, Any] = {
            "valid": True,
            "is_exception": False,
            "slave_id": slave_id,
            "function_code": function_code,
            "raw_payload_hex": payload.hex().upper()
        }

        # Decode standard function codes
        if function_code in (0x03, 0x04):
            if len(payload) == 6:
                # Request frame: [Slave, FC, StartHi, StartLo, QtyHi, QtyLo]
                start_addr, qty = struct.unpack(">HH", payload[2:6])
                result["type"] = "request"
                result["start_address"] = start_addr
                result["quantity"] = qty
            elif len(payload) >= 3:
                # Response frame: [Slave, FC, ByteCount, Data...]
                byte_count = payload[2]
                registers = []
                data_bytes = payload[3:3 + byte_count]
                for i in range(0, len(data_bytes), 2):
                    if i + 1 < len(data_bytes):
                        registers.append(struct.unpack(">H", data_bytes[i:i+2])[0])
                result["type"] = "response"
                result["byte_count"] = byte_count
                result["registers"] = registers

        elif function_code == 0x06:
            addr, val = struct.unpack(">HH", payload[2:6])
            result["address"] = addr
            result["value"] = val

        return result
