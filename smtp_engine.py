"""
Email Auditor Pro — SMTP Validation Engine
Performs DNS MX lookup and lightweight RCPT TO probing.
No passwords are ever used. No account login is attempted.
"""
import asyncio
import aiodns
from datetime import datetime
from typing import Optional, Tuple
from python_socks.async_.asyncio import Proxy
import config


class SMTPValidator:
    """
    Validates email existence by querying MX records and performing
    a minimal SMTP conversation (EHLO → MAIL FROM → RCPT TO → QUIT).
    """

    def __init__(self, mail_from: str = config.DEFAULT_MAIL_FROM, timeout: int = config.SMTP_TIMEOUT):
        self.mail_from = mail_from
        self.timeout = timeout
        self.resolver = aiodns.DNSResolver()

    async def _read_smtp_response(self, reader: asyncio.StreamReader) -> Tuple[str, str]:
        """Read multi-line SMTP response until final line (no dash after code)."""
        lines = []
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=self.timeout)
            if not line:
                raise ConnectionError("SMTP server closed connection unexpectedly")
            decoded = line.decode("utf-8", errors="ignore").rstrip("\r\n")
            lines.append(decoded)
            # SMTP multi-line: 4th char is '-' for continuation
            if len(line) >= 4 and line[3:4] != b"-":
                break
        code = lines[-1][:3]
        message = " ".join(l[4:] for l in lines)
        return code, message

    async def _open_connection(
        self, host: str, port: int, proxy_url: Optional[str] = None
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open a TCP connection, optionally tunnelled through a SOCKS/HTTP proxy."""
        if proxy_url:
            proxy = Proxy.from_url(proxy_url)
            sock = await proxy.connect(dest_host=host, dest_port=port, timeout=self.timeout)
            # Python 3.10+ allows passing an existing socket to open_connection
            return await asyncio.open_connection(sock=sock)
        else:
            return await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=self.timeout
            )

    async def _mx_lookup(self, domain: str) -> Optional[str]:
        """Return the highest-priority MX host for a domain."""
        try:
            mx_records = await self.resolver.query(domain, "MX")
            if not mx_records:
                return None
            # Lower priority number = higher priority
            best = sorted(mx_records, key=lambda r: r.priority)[0]
            return best.host
        except Exception:
            return None

    async def validate(
        self, email: str, proxy_url: Optional[str] = None
    ) -> dict:
        """
        Validate a single email address.
        Returns a dict with keys: email, status, detail, mx, checked_at.
        Statuses: Valid, Invalid, Grey-listed/Retry, Timeout, Error.
        """
        result = {
            "email": email,
            "status": "Error",
            "detail": "",
            "mx": "",
            "checked_at": datetime.utcnow().isoformat(),
        }

        # Basic format sanity check
        if "@" not in email or "." not in email.split("@")[-1]:
            result["status"] = "Invalid"
            result["detail"] = "Malformed email address"
            return result

        domain = email.split("@")[1]

        # MX lookup
        mx_host = await self._mx_lookup(domain)
        if not mx_host:
            result["status"] = "Invalid"
            result["detail"] = "No MX records found for domain"
            return result
        result["mx"] = mx_host

        reader: Optional[asyncio.StreamReader] = None
        writer: Optional[asyncio.StreamWriter] = None

        try:
            reader, writer = await self._open_connection(mx_host, 25, proxy_url)

            # ── Greeting ──
            code, msg = await self._read_smtp_response(reader)
            if not code.startswith("2"):
                result["status"] = "Grey-listed/Retry"
                result["detail"] = f"Greeting rejected: {code} {msg}"
                return result

            # ── EHLO ──
            writer.write(b"EHLO auditor.bot\r\n")
            await writer.drain()
            code, msg = await self._read_smtp_response(reader)
            if not code.startswith("2"):
                # Fallback HELO
                writer.write(b"HELO auditor.bot\r\n")
                await writer.drain()
                code, msg = await self._read_smtp_response(reader)
                if not code.startswith("2"):
                    result["status"] = "Grey-listed/Retry"
                    result["detail"] = f"EHLO/HELO rejected: {code} {msg}"
                    return result

            # ── MAIL FROM ──
            writer.write(f"MAIL FROM:<{self.mail_from}>\r\n".encode())
            await writer.drain()
            code, msg = await self._read_smtp_response(reader)
            if not code.startswith("2"):
                result["status"] = "Grey-listed/Retry"
                result["detail"] = f"MAIL FROM rejected: {code} {msg}"
                return result

            # ── RCPT TO ──
            writer.write(f"RCPT TO:<{email}>\r\n".encode())
            await writer.drain()
            code, msg = await self._read_smtp_response(reader)

            # ── QUIT ──
            writer.write(b"QUIT\r\n")
            await writer.drain()

            # ── Classify ──
            if code.startswith("250"):
                result["status"] = "Valid"
                result["detail"] = msg
            elif code.startswith("550") or code.startswith("551"):
                result["status"] = "Invalid"
                result["detail"] = msg
            elif code.startswith("45") or code.startswith("44") or code.startswith("422"):
                result["status"] = "Grey-listed/Retry"
                result["detail"] = msg
            else:
                result["status"] = "Invalid"
                result["detail"] = f"RCPT TO response: {code} {msg}"

        except asyncio.TimeoutError:
            result["status"] = "Timeout"
            result["detail"] = f"Connection or response timed out after {self.timeout}s"
        except Exception as exc:
            result["status"] = "Error"
            result["detail"] = str(exc)
        finally:
            if writer:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

        return result


class BulkAuditor:
    """
    Orchestrates bulk email validation with dynamic concurrency,
    proxy rotation, and live progress reporting.
    """

    def __init__(
        self,
        proxy_manager,
        concurrency: int = config.MAX_CONCURRENT_CHECKS,
        progress_callback=None,
    ):
        self.proxy_manager = proxy_manager
        self.concurrency = concurrency
        self.progress_callback = progress_callback
        self.validator = SMTPValidator()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    async def run(self, emails: list) -> list:
        """
        Run bulk validation using an asyncio.Queue for memory-safe
        streaming of hundreds of thousands of addresses.
        Returns a list of result dicts.
        """
        total = len(emails)
        processed = 0
        valid = invalid = grey = timeout = 0
        results = []
        start_time = asyncio.get_event_loop().time()

        queue = asyncio.Queue(maxsize=self.concurrency * 2)
        sem = asyncio.Semaphore(self.concurrency)
        lock = asyncio.Lock()

        async def _producer():
            for email in emails:
                if self._cancelled:
                    break
                await queue.put(email)
            await queue.put(None)  # sentinel

        async def _worker():
            nonlocal processed, valid, invalid, grey, timeout
            while True:
                email = await queue.get()
                if email is None:
                    await queue.put(None)  # re-broadcast sentinel for other workers
                    break
                if self._cancelled:
                    queue.task_done()
                    continue

                async with sem:
                    proxy = await self.proxy_manager.get_proxy()
                    try:
                        res = await self.validator.validate(email, proxy)
                    finally:
                        if proxy:
                            await self.proxy_manager.return_proxy(proxy)

                async with lock:
                    results.append(res)
                    processed += 1
                    if res["status"] == "Valid":
                        valid += 1
                    elif res["status"] == "Invalid":
                        invalid += 1
                    elif res["status"] == "Grey-listed/Retry":
                        grey += 1
                    elif res["status"] == "Timeout":
                        timeout += 1

                    if self.progress_callback and (
                        processed % max(1, total // 20) == 0 or processed == total
                    ):
                        elapsed = asyncio.get_event_loop().time() - start_time
                        speed = (processed / elapsed) * 60 if elapsed > 0 else 0
                        await self.progress_callback(
                            total=total,
                            processed=processed,
                            valid=valid,
                            invalid=invalid,
                            grey=grey,
                            timeout=timeout,
                            elapsed=elapsed,
                            speed=speed,
                            final=(processed == total),
                        )
                queue.task_done()

        # Launch producer + worker pool
        workers = [asyncio.create_task(_worker()) for _ in range(self.concurrency)]
        await _producer()
        await asyncio.gather(*workers)

        # Ensure final progress is fired
        if self.progress_callback:
            elapsed = asyncio.get_event_loop().time() - start_time
            speed = (processed / elapsed) * 60 if elapsed > 0 else 0
            await self.progress_callback(
                total=total,
                processed=processed,
                valid=valid,
                invalid=invalid,
                grey=grey,
                timeout=timeout,
                elapsed=elapsed,
                speed=speed,
                final=True,
            )

        return results
