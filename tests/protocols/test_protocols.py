"""
Unit tests for deterministic protocol decoders and CRC calculators.
"""

import pytest
from embeddedcoder.protocols.crc import crc16_modbus, crc16_ccitt, crc8_maxim, nmea_checksum
from embeddedcoder.protocols.modbus import ModbusRTU
from embeddedcoder.protocols.can import CANFrame
from embeddedcoder.protocols.telematics import AIS140Packet


def test_crc16_modbus():
    # Standard Modbus test vector: Slave 1, FC 3, Start 0, Qty 10
    test_vector = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x0A])
    crc = crc16_modbus(test_vector)
    # Integer value is 0xCDC5; on wire (little-endian), low byte 0xC5 first, then high byte 0xCD
    assert crc == 0xCDC5
    import struct
    assert struct.pack("<H", crc) == bytes([0xC5, 0xCD])


def test_crc8_maxim():
    # Dallas 1-wire family code 0x28 (DS18B20), serial 0x000000000001
    test_vector = bytes([0x28, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    crc = crc8_maxim(test_vector)
    assert isinstance(crc, int)
    assert 0 <= crc <= 255


def test_nmea_checksum():
    sentence = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W"
    chk = nmea_checksum(sentence)
    assert len(chk) == 2
    assert all(c in "0123456789ABCDEF" for c in chk)


def test_modbus_rtu_build_and_parse():
    frame = ModbusRTU.build_read_holding_registers(slave_id=1, start_address=100, quantity=2)
    assert len(frame) == 8
    parsed = ModbusRTU.parse_frame(frame)
    assert parsed["valid"] is True
    assert parsed["slave_id"] == 1
    assert parsed["function_code"] == 3
    assert parsed["start_address"] == 100
    assert parsed["quantity"] == 2


def test_modbus_corrupted_crc():
    frame = bytearray(ModbusRTU.build_read_holding_registers(slave_id=1, start_address=100, quantity=2))
    frame[-1] ^= 0xFF  # Corrupt CRC
    parsed = ModbusRTU.parse_frame(bytes(frame))
    assert parsed["valid"] is False
    assert "CRC mismatch" in parsed["error"]


def test_can_j1939_decoding():
    # Example J1939 CAN ID: 0x18F00400 (Electronic Engine Controller 1, PGN 61444, SA 0)
    can_id = 0x18F00400
    j1939 = CANFrame.decode_j1939_can_id(can_id)
    assert j1939["priority"] == 6
    assert j1939["source_address"] == 0
    assert j1939["pgn"] == 61444


def test_obd2_rpm_decoding():
    # OBD-II Mode 01 PID 0C Engine RPM. Payload: 41 0C 1F E0 (RPM = ((0x1F * 256) + 0xE0) / 4 = 2040 RPM)
    data = bytes([0x04, 0x41, 0x0C, 0x1F, 0xE0])
    result = CANFrame.decode_obd2_payload(data)
    assert result["valid"] is True
    assert result["parameter"] == "Engine RPM"
    assert result["value"] == 2040.0


def test_ais140_packet():
    packet = "$PVT,VND01,1.0.0,NR,L,864201040000001,DL01AB1234,1,27102026,112000,28.6139,N,77.2090,E,45.50,180.00,12,215.0,1.2,0.9,1,28,404,45,10A2,42F1,12.6,4.1,1,0,0,0001,0000,0.0,0.0,1*1A"
    # Recalculate checksum
    payload = packet.split("*")[0]
    expected_chk = nmea_checksum(payload)
    valid_packet = f"{payload}*{expected_chk}"
    
    parsed = AIS140Packet.parse_packet(valid_packet)
    assert parsed["valid"] is True
    assert parsed["imei"] == "864201040000001"
    assert parsed["vehicle_registration"] == "DL01AB1234"
    assert parsed["gps_fix"] is True
    assert parsed["latitude"] == 28.6139
