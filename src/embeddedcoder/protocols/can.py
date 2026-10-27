"""
CAN 2.0B, SAE J1939, and OBD-II PID protocol decoding engine.
"""

from typing import Dict, Any, Optional


class CANFrame:
    @staticmethod
    def decode_j1939_can_id(can_id: int) -> Dict[str, Any]:
        """
        Deconstruct 29-bit CAN ID into SAE J1939 components:
        Priority (3 bits), Reserved (1 bit), Data Page (1 bit),
        PDU Format (8 bits), PDU Specific (8 bits), Source Address (8 bits).
        """
        priority = (can_id >> 26) & 0x07
        dp = (can_id >> 24) & 0x01
        pf = (can_id >> 16) & 0xFF
        ps = (can_id >> 8) & 0xFF
        sa = can_id & 0xFF

        # Calculate Parameter Group Number (PGN)
        if pf < 240:
            # PDU1 format (destination specific): PGN = (DP << 16) | (PF << 8)
            pgn = (dp << 16) | (pf << 8)
            da = ps
        else:
            # PDU2 format (broadcast): PGN = (dp << 16) | (pf << 8) | ps
            pgn = (dp << 16) | (pf << 8) | ps
            da = 0xFF  # Global destination

        return {
            "can_id_hex": f"0x{can_id:08X}",
            "priority": priority,
            "data_page": dp,
            "pdu_format": pf,
            "pdu_specific": ps,
            "source_address": sa,
            "destination_address": da,
            "pgn": pgn,
            "pgn_hex": f"0x{pgn:04X}"
        }

    @staticmethod
    def decode_obd2_payload(data: bytes) -> Dict[str, Any]:
        """
        Decode standard SAE J1979 / OBD-II Mode 01 diagnostic payloads.
        Data format: [ByteCount, Mode (e.g. 0x41), PID, A, B, C, D]
        """
        if len(data) < 3:
            return {"valid": False, "error": "Insufficient bytes for OBD-II frame"}

        # If first byte is length (ISO-TP single frame), payload starts at index 1
        offset = 1 if len(data) > 3 and data[0] <= 7 else 0
        service = data[offset]
        pid = data[offset + 1]
        payload = data[offset + 2:]

        result: Dict[str, Any] = {
            "valid": True,
            "service": f"0x{service:02X}",
            "pid": f"0x{pid:02X}"
        }

        # Response to Mode 01 is 0x41
        if service == 0x41:
            if pid == 0x0C and len(payload) >= 2:
                # Engine RPM = ((A * 256) + B) / 4
                a, b = payload[0], payload[1]
                rpm = ((a * 256) + b) / 4.0
                result["parameter"] = "Engine RPM"
                result["value"] = rpm
                result["unit"] = "RPM"

            elif pid == 0x0D and len(payload) >= 1:
                # Vehicle Speed = A km/h
                speed = payload[0]
                result["parameter"] = "Vehicle Speed"
                result["value"] = speed
                result["unit"] = "km/h"

            elif pid == 0x05 and len(payload) >= 1:
                # Coolant Temperature = A - 40 deg C
                temp = payload[0] - 40
                result["parameter"] = "Engine Coolant Temperature"
                result["value"] = temp
                result["unit"] = "°C"

            elif pid == 0x04 and len(payload) >= 1:
                # Calculated Engine Load = (A * 100) / 255 %
                load = (payload[0] * 100.0) / 255.0
                result["parameter"] = "Calculated Engine Load"
                result["value"] = round(load, 2)
                result["unit"] = "%"
            else:
                result["raw_bytes"] = payload.hex().upper()

        return result
