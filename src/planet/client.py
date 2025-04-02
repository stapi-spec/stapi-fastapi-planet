import os
import time

import requests
from fastapi import Request

from settings import Settings

class Client:

    def __init__(self, request: Request):

        token = os.environ.get("BACKEND_TOKEN")
        if authorization := request.headers.get("authorization"):
            token = authorization.replace("Bearer ", "")

        self.token = token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'api-key {self.token}'
        }
        self.orders_url = f'{Settings().api_base_url}/orders/'
        self.iw_search_url = f'{Settings().api_base_url}/imaging-windows/search'

    def get_order(self, order_id: str) -> dict:
        order_url = f'{self.orders_url}{order_id}'
        response = requests.get(order_url, headers=self.headers, allow_redirects=False)
        response.raise_for_status()
        return response.json()

    # todo this is a sync wrapper around an async search, migrate to async
    def get_imaging_windows(self, payload: dict) -> dict:
        iw_url = f'{self.iw_search_url}'
        r = requests.post(iw_url, json=payload, headers=self.headers, allow_redirects=False)
        r.raise_for_status()
        if 'location' not in r.headers:
            raise ValueError(
                "Header 'location' not found: %s, status %s, body %s" % (
                    list(r.headers.keys()), r.status_code, r.text)
            )
        poll_url = r.headers['location']

        while True:
            r = requests.get(poll_url, headers=self.headers)
            r.raise_for_status()
            status = r.json()['status']
            if status == "DONE":
                return r.json()['imaging_windows']
            elif status == 'FAILED':
                raise ValueError(
                    f"Retrieving Imaging Windows failed: {r.json['error_code']} - {r.json['error_message']}'")
            time.sleep(1)
