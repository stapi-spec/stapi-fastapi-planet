import time

import requests
from fastapi import Request

from .settings import Settings


class Client:
    def __init__(self, request: Request):
        authorization = request.headers.get("authorization", "")
        self.token = authorization.replace("Bearer ", "").replace("api-key ", "")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"api-key {self.token}",
        }
        self.orders_url = f"{Settings().api_base_url}/orders/"
        self.iw_search_url = f"{Settings().api_base_url}/imaging-windows/search"
        self.products_url = f"{Settings().api_base_url}/products"

    def get_order(self, order_id: str) -> dict:
        order_url = f"{self.orders_url}{order_id}"
        response = requests.get(order_url, headers=self.headers, allow_redirects=False)
        response.raise_for_status()
        return response.json()

    # todo this is a sync wrapper around an async search, migrate to async
    def get_imaging_windows(self, payload: dict) -> dict:
        r = requests.post(
            self.iw_search_url,
            json=payload,
            headers=self.headers,
            allow_redirects=False,
        )
        r.raise_for_status()
        if "location" not in r.headers:
            raise ValueError(
                f"Header 'location' not found: {list(r.headers.keys())}, status {r.status_code}, body {r.text}"
            )
        poll_url = f"{Settings().api_domain}{r.headers['location']}"

        while True:
            print("polling", poll_url)
            r = requests.get(poll_url, headers=self.headers)
            r.raise_for_status()
            status = r.json()["status"]
            if status == "DONE":
                print("done polling")
                return r.json()["imaging_windows"]
            elif status == "FAILED":
                raise ValueError(
                    f"Retrieving Imaging Windows failed: {r.json()['error_code']} - {r.json()['error_message']}'"
                )
            time.sleep(1)

    def get_products(self) -> dict:
        r = requests.get(self.products_url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def create_order(self, payload: dict) -> dict:
        print("order payload", payload)
        r = requests.post(
            self.orders_url, json=payload, headers=self.headers, allow_redirects=False
        )
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            print(r.text)
            raise e
        return r.json()
