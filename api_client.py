import time
import requests
from config import BASE_URL, REQUEST_DELAY, MAX_RETRIES

REQUEST_TIMEOUT = 30


class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.csrf_token = None
        self._last_request_time = 0

    def _throttle(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.request(method, url, **kwargs)
                return resp
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait = 3 * (attempt + 1)
                print(f"  网络错误，{wait}秒后重试 ({attempt+1}/{MAX_RETRIES}): {type(e).__name__}")
                time.sleep(wait)

    def _fetch_csrf(self):
        resp = self._request_with_retry("GET", f"{BASE_URL}/auth/csrf")
        self.csrf_token = resp.headers.get("X-Csrf-Token") or resp.headers.get("X-CSRF-Token")
        if not self.csrf_token:
            raise RuntimeError("无法获取 CSRF Token")
        self.session.headers["X-CSRF-Token"] = self.csrf_token

    def login(self, email: str, password: str) -> dict:
        self._fetch_csrf()
        resp = self._request_with_retry(
            "POST", f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if resp.status_code != 200:
            raise RuntimeError(f"登录失败: {resp.text}")
        user = resp.json()
        print(f"登录成功: {user.get('username')} (ID: {user.get('id')})")
        return user

    def get_me(self) -> dict:
        resp = self._request_with_retry("GET", f"{BASE_URL}/auth/me")
        if resp.status_code == 401:
            return None
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, params: dict = None) -> dict:
        self._throttle()
        url = f"{BASE_URL}{path}"
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._request_with_retry("GET", url, params=params)
                resp.raise_for_status()
                return resp.json()
            except requests.HTTPError as e:
                if resp.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"  请求频率限制，{wait}秒后重试...")
                    time.sleep(wait)
                    continue
                raise

    def get_paginated(self, path: str, params: dict = None, page_size: int = 50):
        p = dict(params or {})
        p.setdefault("page_size", page_size)
        p.setdefault("page", 1)
        data = self.get(path, p)
        if isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            total = data.get("total", len(items))
            return items, total, data
        elif isinstance(data, list):
            return data, len(data), {}
        return [], 0, {}

    def get_all_pages(self, path: str, params: dict = None, page_size: int = 50,
                      existing_ids: set = None):
        all_items = []
        page = 1
        stale_pages = 0
        max_stale_pages = 3
        while True:
            p = dict(params or {})
            p["page"] = page
            p["page_size"] = page_size
            items, total, raw = self.get_paginated(path, p, page_size)
            all_items.extend(items)
            print(f"  已获取 {len(all_items)}/{total} 条", end="")

            # 增量模式：如果一整页全部已存在，连续多页后提前终止
            if existing_ids is not None and items:
                new_in_page = sum(1 for it in items if it.get("id") not in existing_ids)
                if new_in_page == 0:
                    stale_pages += 1
                    print(f" (全部已存在, 连续第{stale_pages}页)")
                    if stale_pages >= max_stale_pages:
                        print(f"  连续 {max_stale_pages} 页无新数据，提前结束")
                        break
                else:
                    stale_pages = 0
                    print(f" (本页新增 {new_in_page})")
            else:
                print()

            if len(all_items) >= total or not items:
                break
            page += 1
        return all_items
