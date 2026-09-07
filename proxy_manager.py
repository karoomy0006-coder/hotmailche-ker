"""
Email Auditor Pro — Proxy Manager
Parses, validates, and rotates HTTP/SOCKS4/SOCKS5 proxies.
"""
import asyncio
import re
from typing import Optional, List
from python_socks.async_.asyncio import Proxy
import config


class ProxyManager:
    """Manages a pool of validated proxies using asyncio.Queue for thread-safe rotation."""

    def __init__(self):
        self._raw_proxies: List[str] = []
        self._valid_queue: asyncio.Queue[str] = asyncio.Queue()
        self._invalid_count = 0
        self._valid_count = 0

    # ─── Parsing ───
    @staticmethod
    def _parse_proxy(line: str) -> Optional[str]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        # Supported formats:
        #   ip:port
        #   user:pass@ip:port
        #   http://ip:port
        #   http://user:pass@ip:port
        #   socks4://ip:port
        #   socks5://user:pass@ip:port
        if re.match(r"^(https?|socks4|socks5)://", line):
            return line
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d+$", line):
            return f"http://{line}"
        if re.match(r"^[^:]+:[^@]+@\d{1,3}(\.\d{1,3}){3}:\d+$", line):
            return f"http://{line}"
        # Try loose match
        if ":" in line:
            return f"http://{line}"
        return None

    def load_from_text(self, text: str) -> int:
        """Load raw proxies from a multi-line string. Returns count."""
        self._raw_proxies.clear()
        for line in text.splitlines():
            parsed = self._parse_proxy(line)
            if parsed:
                self._raw_proxies.append(parsed)
        return len(self._raw_proxies)

    # ─── Validation ───
    async def _test_proxy(self, proxy_url: str) -> bool:
        """Validate a proxy by opening a TCP tunnel to a known mail server."""
        try:
            proxy = Proxy.from_url(proxy_url)
            sock = await proxy.connect(
                dest_host=config.PROXY_VALIDATE_HOST,
                dest_port=config.PROXY_VALIDATE_PORT,
                timeout=config.PROXY_CHECK_TIMEOUT,
            )
            sock.close()
            return True
        except Exception:
            return False

    async def validate_all(self, progress_callback=None):
        """Validate all loaded proxies concurrently."""
        self._valid_count = 0
        self._invalid_count = 0
        # Drain existing queue
        while not self._valid_queue.empty():
            try:
                self._valid_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        sem = asyncio.Semaphore(200)  # limit concurrent validation

        async def _check_one(proxy_url: str):
            async with sem:
                ok = await self._test_proxy(proxy_url)
                if ok:
                    await self._valid_queue.put(proxy_url)
                    self._valid_count += 1
                else:
                    self._invalid_count += 1
                if progress_callback:
                    await progress_callback(self._valid_count + self._invalid_count)

        await asyncio.gather(*[_check_one(p) for p in self._raw_proxies])

    # ─── Rotation ───
    async def get_proxy(self) -> Optional[str]:
        """Fetch a proxy from the pool (FIFO). Returns None if pool empty."""
        try:
            return self._valid_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def return_proxy(self, proxy_url: str):
        """Return a proxy to the pool after use (allows reuse)."""
        await self._valid_queue.put(proxy_url)

    @property
    def valid_count(self) -> int:
        return self._valid_count

    @property
    def invalid_count(self) -> int:
        return self._invalid_count

    @property
    def total_raw(self) -> int:
        return len(self._raw_proxies)

    def is_empty(self) -> bool:
        return self._valid_queue.empty()
