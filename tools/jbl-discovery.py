#!/usr/bin/env python3
"""
JBL AV Receiver Discovery Script - Standalone Version
No external dependencies required (Python 3.7+ standard library only).

Discovers ALL device capabilities for comprehensive debugging and validation.

Usage:
    python jbl-discovery.py <device_ip> [port]

Example:
    python jbl-discovery.py 192.168.1.100
    python jbl-discovery.py 192.168.1.100 50000

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Optional

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_info(msg: str):
    """Print info message in yellow."""
    print(f"{Colors.YELLOW}ℹ{Colors.RESET} {msg}")

def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")

def format_hex(data: bytes) -> str:
    """Format bytes as hex string."""
    return ' '.join(f'{b:02X}' for b in data)

class JBLProtocol:
    """Simplified JBL protocol handler for discovery."""

    CMD_START = 0x23
    RESP_START = bytes([0x02, 0x23])
    END = 0x0D
    REQUEST_DATA = 0xF0

    # Command IDs
    COMMANDS = {
        0x00: "Power",
        0x01: "Display Dim",
        0x02: "Software Version",
        0x04: "IR Simulate",
        0x05: "Input Source",
        0x06: "Volume",
        0x07: "Mute",
        0x08: "Surround Mode",
        0x09: "Party Mode",
        0x0A: "Party Volume",
        0x0B: "Treble EQ",
        0x0C: "Bass EQ",
        0x0D: "Room EQ",
        0x0E: "Dialog Enhanced",
        0x0F: "Dolby Audio Mode",
        0x10: "DRC",
        0x11: "Streaming State",
        0x50: "Initialization",
        0x51: "Heartbeat",
        0x52: "Reboot",
        0x53: "Factory Reset",
    }

    MODELS = {
        0x01: "MA510",
        0x02: "MA710",
        0x03: "MA7100HP",
        0x04: "MA9100HP",
    }

    INPUT_SOURCES = {
        0x01: "TV (ARC)",
        0x02: "HDMI 1",
        0x03: "HDMI 2",
        0x04: "HDMI 3",
        0x05: "HDMI 4",
        0x06: "HDMI 5",
        0x07: "HDMI 6",
        0x08: "Coaxial",
        0x09: "Optical",
        0x0A: "Analog 1",
        0x0B: "Analog 2",
        0x0C: "Phono",
        0x0D: "Bluetooth",
        0x0E: "Network",
    }

    SURROUND_MODES = {
        0x01: "Dolby Surround",
        0x02: "DTS Neural:X",
        0x03: "Stereo 2.0",
        0x04: "Stereo 2.1",
        0x05: "All Stereo",
        0x06: "Native",
        0x07: "Dolby Pro Logic II",
    }

    @staticmethod
    def build_command(cmd_id: int, *data: int) -> bytes:
        """Build a JBL command message."""
        data_len = len(data)
        command = bytes([JBLProtocol.CMD_START, cmd_id, data_len])
        command += bytes(data)
        command += bytes([JBLProtocol.END])
        return command

    @staticmethod
    def parse_response(data: bytes) -> Optional[dict[str, Any]]:
        """Parse a JBL response message."""
        if len(data) < 5:
            return None

        if data[0:2] != JBLProtocol.RESP_START:
            return None

        if data[-1] != JBLProtocol.END:
            return None

        cmd_id = data[2]
        rsp_code = data[3]
        data_len = data[4]

        response_data = []
        if data_len > 0:
            if len(data) >= 5 + data_len + 1:
                response_data = list(data[5:5 + data_len])

        return {
            "cmd_id": cmd_id,
            "rsp_code": rsp_code,
            "data": response_data,
        }


async def test_tcp_connection(host: str, port: int) -> tuple[bool, str]:
    """Test basic TCP connection."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        return True, "Connection successful"
    except asyncio.TimeoutError:
        return False, "Connection timeout (5s)"
    except ConnectionRefusedError:
        return False, "Connection refused - device may be off or IP control disabled"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


async def send_command(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                       command: bytes, timeout: float = 2.0) -> Optional[bytes]:
    """Send command and wait for response."""
    try:
        writer.write(command)
        await writer.drain()

        # Read response with timeout
        response = await asyncio.wait_for(
            reader.read(1024),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        return None


async def discover_jbl_device(host: str, port: int = 50000) -> dict[str, Any]:
    """Comprehensive discovery of JBL AV receiver capabilities."""

    print_section(f"JBL AV RECEIVER DISCOVERY: {host}:{port}")

    report = {
        "discovery_info": {
            "host": host,
            "port": port,
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.0.0"
        },
        "connection": {
            "tcp_reachable": False,
            "error": None
        },
        "device_info": {
            "model_id": None,
            "model_name": "Unknown",
            "software_version": None,
        },
        "current_state": {
            "power": None,
            "volume": None,
            "muted": None,
            "input_source_id": None,
            "input_source_name": None,
            "surround_mode_id": None,
            "surround_mode_name": None,
            "party_mode": None,
            "display_brightness": None,
        },
        "supported_commands": {},
        "raw_responses": {},
        "errors": []
    }

    # ========================================
    # 1. TCP CONNECTION TEST
    # ========================================
    print_section("1. TCP CONNECTION TEST")

    success, message = await test_tcp_connection(host, port)
    report["connection"]["tcp_reachable"] = success
    report["connection"]["message"] = message

    if success:
        print_success(f"TCP connection to {host}:{port} successful")
    else:
        print_error(f"TCP connection failed: {message}")
        print_info("Please verify:")
        print_info("  1. Device is powered on")
        print_info("  2. IP address is correct")
        print_info("  3. IP control is enabled (not in 'Green' standby mode)")
        print_info("  4. Device is on same network")
        return report

    # ========================================
    # 2. ESTABLISH PERSISTENT CONNECTION
    # ========================================
    print_section("2. ESTABLISHING CONNECTION")

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=10.0
        )
        print_success("Connection established")
    except Exception as e:
        print_error(f"Failed to establish connection: {e}")
        report["errors"].append(f"Connection failed: {e}")
        return report

    # ========================================
    # 3. INITIALIZATION & MODEL DETECTION
    # ========================================
    print_section("3. DEVICE INITIALIZATION")

    init_cmd = JBLProtocol.build_command(0x50, JBLProtocol.REQUEST_DATA)
    print(f"  Sending initialization command: {format_hex(init_cmd)}")

    response = await send_command(reader, writer, init_cmd, timeout=2.0)

    if response:
        print_success(f"Response received: {format_hex(response)}")
        report["raw_responses"]["initialization"] = format_hex(response)

        parsed = JBLProtocol.parse_response(response)
        if parsed and len(parsed["data"]) > 0:
            model_id = parsed["data"][0]
            model_name = JBLProtocol.MODELS.get(model_id, f"Unknown (0x{model_id:02X})")
            report["device_info"]["model_id"] = model_id
            report["device_info"]["model_name"] = model_name
            report["supported_commands"][0x50] = "Initialization"
            print_success(f"Model detected: {Colors.BOLD}{model_name}{Colors.RESET} (ID: 0x{model_id:02X})")
    else:
        print_error("No response to initialization command")
        report["errors"].append("No initialization response")

    # Small delay
    await asyncio.sleep(0.5)

    # ========================================
    # 4. QUERY ALL DEVICE STATE
    # ========================================
    print_section("4. QUERYING DEVICE STATE")

    state_queries = [
        (0x00, "Power State"),
        (0x06, "Volume"),
        (0x07, "Mute Status"),
        (0x05, "Input Source"),
        (0x08, "Surround Mode"),
        (0x01, "Display Brightness"),
        (0x09, "Party Mode"),
        (0x0B, "Treble EQ"),
        (0x0C, "Bass EQ"),
        (0x0D, "Room EQ"),
        (0x0E, "Dialog Enhanced"),
        (0x0F, "Dolby Audio Mode"),
        (0x10, "DRC"),
    ]

    for cmd_id, description in state_queries:
        cmd = JBLProtocol.build_command(cmd_id, JBLProtocol.REQUEST_DATA)
        print(f"\n  {description} (0x{cmd_id:02X}):")
        print(f"    Sending: {format_hex(cmd)}")

        response = await send_command(reader, writer, cmd, timeout=1.0)

        if response:
            print_success(f"Response: {format_hex(response)}")
            report["raw_responses"][f"cmd_0x{cmd_id:02X}"] = format_hex(response)
            report["supported_commands"][cmd_id] = description

            parsed = JBLProtocol.parse_response(response)
            if parsed and parsed["rsp_code"] == 0x00:
                data = parsed["data"]

                # Interpret data based on command
                if cmd_id == 0x00 and len(data) > 0:
                    report["current_state"]["power"] = data[0] == 0x01
                    print(f"    Power: {Colors.CYAN}{'ON' if data[0] == 0x01 else 'OFF'}{Colors.RESET}")

                elif cmd_id == 0x06 and len(data) > 0:
                    report["current_state"]["volume"] = data[0]
                    print(f"    Volume: {Colors.CYAN}{data[0]}/99{Colors.RESET}")

                elif cmd_id == 0x07 and len(data) > 0:
                    report["current_state"]["muted"] = data[0] == 0x01
                    print(f"    Muted: {Colors.CYAN}{'YES' if data[0] == 0x01 else 'NO'}{Colors.RESET}")

                elif cmd_id == 0x05 and len(data) > 0:
                    source_id = data[0]
                    source_name = JBLProtocol.INPUT_SOURCES.get(source_id, f"Unknown (0x{source_id:02X})")
                    report["current_state"]["input_source_id"] = source_id
                    report["current_state"]["input_source_name"] = source_name
                    print(f"    Input: {Colors.CYAN}{source_name}{Colors.RESET}")

                elif cmd_id == 0x08 and len(data) > 0:
                    mode_id = data[0]
                    mode_name = JBLProtocol.SURROUND_MODES.get(mode_id, f"Unknown (0x{mode_id:02X})")
                    report["current_state"]["surround_mode_id"] = mode_id
                    report["current_state"]["surround_mode_name"] = mode_name
                    print(f"    Surround: {Colors.CYAN}{mode_name}{Colors.RESET}")

                elif cmd_id == 0x01 and len(data) > 0:
                    brightness_levels = ["Off", "Dim", "Mid", "Bright"]
                    brightness = brightness_levels[data[0]] if data[0] < len(brightness_levels) else f"Unknown ({data[0]})"
                    report["current_state"]["display_brightness"] = data[0]
                    print(f"    Display: {Colors.CYAN}{brightness}{Colors.RESET}")

                elif cmd_id == 0x09 and len(data) > 0:
                    report["current_state"]["party_mode"] = data[0] == 0x01
                    print(f"    Party Mode: {Colors.CYAN}{'ON' if data[0] == 0x01 else 'OFF'}{Colors.RESET}")

                else:
                    print(f"    Data: {Colors.CYAN}{[f'0x{b:02X}' for b in data]}{Colors.RESET}")
        else:
            print_info(f"No response (timeout) - command may not be supported")

        await asyncio.sleep(0.1)

    # ========================================
    # 5. SOFTWARE VERSION QUERY
    # ========================================
    print_section("5. SOFTWARE VERSION")

    version_types = [
        (0xF0, "IP Control"),
        (0xF1, "Host"),
        (0xF2, "DSP"),
        (0xF3, "OSD"),
        (0xF4, "Network"),
    ]

    for ver_type, ver_name in version_types:
        cmd = JBLProtocol.build_command(0x02, ver_type)
        print(f"\n  {ver_name} Version (0x{ver_type:02X}):")
        print(f"    Sending: {format_hex(cmd)}")

        response = await send_command(reader, writer, cmd, timeout=1.0)

        if response:
            print_success(f"Response: {format_hex(response)}")
            report["raw_responses"][f"version_0x{ver_type:02X}"] = format_hex(response)

            parsed = JBLProtocol.parse_response(response)
            if parsed and parsed["rsp_code"] == 0x00 and len(parsed["data"]) > 0:
                # Version is typically ASCII string
                try:
                    version_str = ''.join(chr(b) for b in parsed["data"] if 32 <= b <= 126)
                    print(f"    Version: {Colors.CYAN}{version_str}{Colors.RESET}")
                    if ver_type == 0xF0:
                        report["device_info"]["software_version"] = version_str
                except:
                    print(f"    Data: {[f'0x{b:02X}' for b in parsed['data']]}")
        else:
            print_info(f"No response")

        await asyncio.sleep(0.1)

    # ========================================
    # 6. HEARTBEAT TEST
    # ========================================
    print_section("6. HEARTBEAT TEST")

    heartbeat_cmd = JBLProtocol.build_command(0x51)
    print(f"  Sending heartbeat: {format_hex(heartbeat_cmd)}")

    response = await send_command(reader, writer, heartbeat_cmd, timeout=1.0)

    if response:
        print_success(f"Heartbeat acknowledged: {format_hex(response)}")
        report["raw_responses"]["heartbeat"] = format_hex(response)
        report["supported_commands"][0x51] = "Heartbeat"
    else:
        print_info("No heartbeat response")

    # ========================================
    # 7. CLOSE CONNECTION
    # ========================================
    print_section("7. CLOSING CONNECTION")

    writer.close()
    await writer.wait_closed()
    print_success("Connection closed gracefully")

    return report


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Error: Missing device IP address{Colors.RESET}")
        print(f"\nUsage: python {sys.argv[0]} <device_ip> [port]")
        print(f"Example: python {sys.argv[0]} 192.168.1.100")
        print(f"Example: python {sys.argv[0]} 192.168.1.100 50000")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 50000

    # Run discovery
    report = await discover_jbl_device(host, port)

    # ========================================
    # FINAL REPORT
    # ========================================
    print_section("DISCOVERY COMPLETE")

    print(f"\n{Colors.BOLD}Device Summary:{Colors.RESET}")
    print(f"  Model: {Colors.CYAN}{report['device_info']['model_name']}{Colors.RESET}")
    print(f"  Software Version: {Colors.CYAN}{report['device_info'].get('software_version', 'Unknown')}{Colors.RESET}")
    print(f"  Power: {Colors.CYAN}{report['current_state'].get('power', 'Unknown')}{Colors.RESET}")
    print(f"  Volume: {Colors.CYAN}{report['current_state'].get('volume', 'Unknown')}{Colors.RESET}")
    print(f"  Input: {Colors.CYAN}{report['current_state'].get('input_source_name', 'Unknown')}{Colors.RESET}")
    print(f"  Surround: {Colors.CYAN}{report['current_state'].get('surround_mode_name', 'Unknown')}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Supported Commands ({len(report['supported_commands'])}):{Colors.RESET}")
    for cmd_id, cmd_name in sorted(report['supported_commands'].items()):
        print(f"  ✓ 0x{cmd_id:02X}: {cmd_name}")

    # Save report to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jbl_discovery_{host.replace('.', '_')}_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n{Colors.GREEN}Full report saved to: {Colors.BOLD}{filename}{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Please send this JSON file to the integration developer for analysis.{Colors.RESET}")
    print(f"{Colors.YELLOW}This will help diagnose any compatibility issues with your specific JBL model.{Colors.RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Discovery interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
