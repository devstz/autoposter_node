from __future__ import annotations

import platform
import re
import subprocess
import socket
from dataclasses import dataclass
from typing import Optional


class SystemService:
    def detect_primary_ip(self) -> str:
        ip = self._detect_with_psutil()
        if ip:
            return ip

        ip = self._detect_with_ip_route()
        if ip:
            return ip

        ip = self._detect_with_route_get()
        if ip:
            return ip

        return "0.0.0.0"

    @staticmethod
    def _detect_with_psutil() -> Optional[str]:
        try:
            import psutil
        except ImportError:
            return None

        inet_family = getattr(socket, "AF_INET", None)
        for addrs in psutil.net_if_addrs().values():
            for addr in addrs:
                if inet_family is not None and getattr(addr, "family", None) != inet_family:
                    continue
                address = getattr(addr, "address", "")
                if address and not address.startswith("127."):
                    return address
        return None

    @staticmethod
    def _detect_with_ip_route() -> Optional[str]:
        try:
            result = subprocess.run(
                ["/sbin/ip", "route", "get", "1"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ["ip", "route", "get", "1"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                return None

        if result.returncode != 0:
            return None

        match = re.search(r"src\s+(\S+)", result.stdout)
        if match:
            ip = match.group(1)
            if ip and not ip.startswith("127."):
                return ip
        return None

    @staticmethod
    def _detect_with_route_get() -> Optional[str]:
        if platform.system() != "Darwin":
            return None

        try:
            result = subprocess.run(
                ["/usr/sbin/route", "-n", "get", "default"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None

        if result.returncode != 0:
            return None

        match = re.search(r"interface:\s*(\S+)", result.stdout)
        if not match:
            return None

        interface = match.group(1)
        for candidate in (
            ["/usr/sbin/ipconfig", "getifaddr", interface],
            ["/sbin/ifconfig", interface],
        ):
            try:
                addr_result = subprocess.run(
                    candidate,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                continue

            if addr_result.returncode != 0:
                continue

            if "getifaddr" in candidate:
                ip = addr_result.stdout.strip()
                if ip and not ip.startswith("127."):
                    return ip

            match_ip = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", addr_result.stdout)
            if match_ip:
                ip = match_ip.group(1)
                if ip and not ip.startswith("127."):
                    return ip

        return None

    @dataclass
    class UpdateCommandResult:
        """Result of update command execution."""
        success: bool
        exit_code: int
        stdout: str
        stderr: str

    @staticmethod
    def execute_update_command() -> "SystemService.UpdateCommandResult":
        """
        Execute update command: cd /opt/autoposter_node/ && git pull && systemctl restart autoposter.service
        
        Returns:
            UpdateCommandResult with execution details
        """
        command = "cd /opt/autoposter_node/ && git pull && systemctl restart autoposter.service"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )
            
            return SystemService.UpdateCommandResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return SystemService.UpdateCommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Command execution timeout (exceeded 5 minutes)",
            )
        except Exception as e:
            return SystemService.UpdateCommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Exception during command execution: {str(e)}",
            )


