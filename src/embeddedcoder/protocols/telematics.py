"""
AIS-140 Vehicle Telematics Protocol Parser and Builder (MoRTH Standard).
Decodes and constructs standard GPS tracking, emergency alerts, health frames, and checksums.
"""

from typing import Dict, Any, Optional
from embeddedcoder.protocols.crc import nmea_checksum


class AIS140Packet:
    @staticmethod
    def parse_packet(packet_str: str) -> Dict[str, Any]:
        """
        Parse and validate an AIS-140 telemetry string.
        Format: $Header,VendorID,FirmwareVer,PacketType,PacketStatus,IMEI,VehicleReg,GPSFix,Date,Time,Lat,LatDir,Lon,LonDir,Speed,Heading,Satellites,Altitude,PDOP,HDOP,Network,GSM_Signal,MCC,MNC,LAC,CellID,MainPower,InternalBattery,Ignition,EmergencyStatus,TamperAlert,DigitalInputs,DigitalOutputs,Analog1,Analog2,FrameNumber*Checksum
        """
        raw = packet_str.strip()
        if not raw.startswith("$"):
            return {"valid": False, "error": "Packet must start with '$'"}
        if "*" not in raw:
            return {"valid": False, "error": "Missing checksum delimiter '*'"}

        payload, received_checksum = raw.split("*", 1)
        expected_checksum = nmea_checksum(payload)

        if received_checksum.strip().upper() != expected_checksum:
            return {
                "valid": False,
                "error": f"Checksum mismatch: expected {expected_checksum}, received {received_checksum.strip()}",
                "expected_checksum": expected_checksum,
                "received_checksum": received_checksum.strip()
            }

        fields = payload[1:].split(",")
        if len(fields) < 15:
            return {"valid": False, "error": f"Malformed AIS-140 packet: expected at least 15 fields, got {len(fields)}"}

        try:
            return {
                "valid": True,
                "header": fields[0],
                "vendor_id": fields[1] if len(fields) > 1 else "",
                "firmware_version": fields[2] if len(fields) > 2 else "",
                "packet_type": fields[3] if len(fields) > 3 else "NR",
                "imei": fields[5] if len(fields) > 5 else "",
                "vehicle_registration": fields[6] if len(fields) > 6 else "",
                "gps_fix": fields[7] == "1" if len(fields) > 7 else False,
                "date": fields[8] if len(fields) > 8 else "",
                "time": fields[9] if len(fields) > 9 else "",
                "latitude": float(fields[10]) if len(fields) > 10 and fields[10] else 0.0,
                "lat_direction": fields[11] if len(fields) > 11 else "N",
                "longitude": float(fields[12]) if len(fields) > 12 and fields[12] else 0.0,
                "lon_direction": fields[13] if len(fields) > 13 else "E",
                "speed_kmh": float(fields[14]) if len(fields) > 14 and fields[14] else 0.0,
                "emergency_status": fields[29] == "1" if len(fields) > 29 else False,
                "ignition": fields[28] == "1" if len(fields) > 28 else False,
                "checksum": expected_checksum
            }
        except Exception as e:
            return {"valid": False, "error": f"Error parsing fields: {str(e)}"}

    @staticmethod
    def build_packet(fields_dict: Dict[str, Any]) -> str:
        """Construct a validated AIS-140 packet with calculated checksum."""
        order = [
            fields_dict.get("header", "PVT"),
            fields_dict.get("vendor_id", "VND01"),
            fields_dict.get("firmware_version", "1.0.0"),
            fields_dict.get("packet_type", "NR"),
            fields_dict.get("packet_status", "L"),
            fields_dict.get("imei", "864201040000001"),
            fields_dict.get("vehicle_registration", "DL01AB1234"),
            "1" if fields_dict.get("gps_fix", True) else "0",
            fields_dict.get("date", "27102026"),
            fields_dict.get("time", "112000"),
            f"{fields_dict.get('latitude', 28.6139):.4f}",
            fields_dict.get("lat_direction", "N"),
            f"{fields_dict.get('longitude', 77.2090):.4f}",
            fields_dict.get("lon_direction", "E"),
            f"{fields_dict.get('speed_kmh', 0.0):.2f}",
            f"{fields_dict.get('heading', 0.0):.2f}",
            str(fields_dict.get("satellites", 12)),
            f"{fields_dict.get('altitude', 215.0):.1f}",
            "1.2", "0.9", "1", "28", "404", "45", "10A2", "42F1",
            f"{fields_dict.get('main_power', 12.6):.1f}",
            f"{fields_dict.get('battery_power', 4.1):.1f}",
            "1" if fields_dict.get("ignition", False) else "0",
            "1" if fields_dict.get("emergency_status", False) else "0",
            "0", "0001", "0000", "0.0", "0.0",
            str(fields_dict.get("frame_number", 1))
        ]
        payload = "$" + ",".join(order)
        chk = nmea_checksum(payload)
        return f"{payload}*{chk}"
