import sys

sys.path.append("..")

import os
import requests
import json
from utils import setup_logger
from typing import List
from pprint import pprint


class WixAPI:
    """
    WixAPI class that handles communication with the Wix API.
    """

    def __init__(self):
        """
        Initialize the WixAPI object with the API key and site id from the environment variables
        """
        self.api_key = os.getenv("WIX_API_KEY")
        assert self.api_key, "WIX_API_KEY environment variable not set"
        self.site_id = os.getenv("WIX_SITE_ID")
        assert self.site_id, "WIX_SITE_ID environment variable not set"
        self.base_url_v2 = "https://www.wixapis.com/stores/v2/"
        self.base_url_v1 = "https://www.wixapis.com/stores/v1/"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
            "wix-site-id": self.site_id,
        }
        self.logger = setup_logger("wix_api", "../logs/wix_api.log")

    def _handle_response(self, response):
        if response.status_code != 200:
            self.logger.error(f"Request failed with status code {response.status_code}")
        try:
            return response
        except json.JSONDecodeError:
            self.logger.error("Failed to decode API response")

    def _exclude_header_key(self, key):
        """
        Exclude a key from the headers dictionary.
        :param key: The key to exclude.
        """
        assert (
            key in self.headers.keys()
        ), f"Key {key} not in headers, should be one of {self.headers.keys()}"
        adapted_headers = {k: value for k, value in self.headers.items() if k != key}
        return adapted_headers


class Orders(WixAPI):
    """
    Orders class that handles communication with the Wix Orders API.
    """

    def __init__(self):
        super().__init__()

    def get_paid_orders(self, limit=2):
        """
        Get paid orders from the Wix API.
        :param limit: The number of orders to get, max 100
        """
        assert limit <= 100, "Limit must be less than or equal to 100"
        endpoint = f"{self.base_url_v2}orders/query"
        data = {
            "query": {
                "filter": '{"paymentStatus": "PAID"}',  # could be expanded but not useful atm
                "paging": {"limit": limit},
                "sort": '[{"number": "desc"}]',
            }
        }
        try:
            response = requests.post(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            self.logger.info(f"Orders status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))

    def get_order(self, orderId: str):
        """
        Get an order from the Wix API.
        :param orderId: The order ID to get.
        """
        endpoint = f"{self.base_url_v2}orders/{orderId}"
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
            )
            self.logger.info(f"get_order status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))


class Inventory(WixAPI):
    """
    Inventory class that handles communication with the Wix Inventory API.
    """

    def __init__(self):
        super().__init__()

    def get_inventory_variants(self, productId, variantId: List[str] = []):
        """
        Get inventory of variants for a product from the Wix API.
        :param productId: The product ID to get inventory of variants for.
        """
        endpoint = f"{self.base_url_v2}inventoryItems/product/{productId}/getVariants"
        data = (
            {
                "variantId": variantId,
            }
            if variantId != []
            else {}
        )

        try:
            response = requests.post(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            self.logger.info(
                f"get_inventory_variants status code: {response.status_code}"
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))

    def decrease_inventory(self, productId: str, variantId: str, quantity: int):
        """
        Decrease inventory of a variant of a product by the given quantity.
        :param productId: The product ID to decrease inventory of.
        :param variantId: The variant ID to decrease inventory of.
        :param quantity: The quantity to decrease inventory by (i.e. positive integer)
        """
        endpoint = f"{self.base_url_v2}inventoryItems/decrement"
        data = {
            "decrementData": [
                {
                    "productId": productId,
                    "decrementBy": quantity,
                }
            ]
        }
        if variantId is not None:
            data["decrementData"][0]["variantId"] = variantId
        else:
            data["decrementData"][0][
                "variantId"
            ] = "00000000-0000-0000-0000-000000000000"
        try:
            response = requests.post(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            response.raise_for_status()
            self.logger.info(f"Decrease inventory status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))


class Products(WixAPI):
    """
    Products class that handles communication with the Wix Orders API.
    Queries are pretty powerful to obtain products with many custom filters.
    """

    def __init__(self):
        super().__init__()

    def get_product(self, productId: str):
        endpoint = f"{self.base_url_v1}products/{productId}"
        headers = self._exclude_header_key("Content-Type")
        try:
            response = requests.get(
                endpoint,
                headers=headers,
            )
            self.logger.info(f"get_product status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))

    def query_products(
        self,
        includeVariants: bool = False,
        includeHiddenProducts: bool = False,
        query={},
    ):
        """
        Get products from the Wix API using a Wix query (see docs).
        :param includeVariants: Whether to include variants in the response.
        :param includeHiddenProducts: Whether to include hidden products in the response.
        :param query: The query to use to get products. E.g. {"filter": '{"id": productId}'}
        """
        endpoint = f"{self.base_url_v1}products/query"
        data = {
            "query": query,
            "includeVariants": includeVariants,
            "includeHiddenProducts": includeHiddenProducts,
        }
        try:
            response = requests.post(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            if response.json()["totalResults"] > 100:
                self.logger.warning(
                    "More than 100 products were queried, need to implement pagination"
                )
            self.logger.info(f"query_products status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))

    def create_product(
        self,
        name="",
        slug="",
        price=0.0,
        sku="",
        visible=True,
        manage_variants=True,
        item_cost=0.0,
        description="",
        product_options=[],
        seo_data="",
    ):
        "TO DO: update"
        product = {
            "name": name,
            "slug": slug,
            "productType": "physical",
            "priceData": {"price": price},
            "costAndProfitData": {
                "itemCost": item_cost,
            },
            "description": description,
            "sku": sku,
            "visible": visible,
            "brand": "Naos Optics",
            "manageVariants": manage_variants,
            "productOptions": product_options,
            "seoData": seo_data,
        }

        product = {"product": product}
        endpoint = f"{self.base_url_v1}products"
        try:
            response = requests.post(
                endpoint, headers=self.headers, data=json.dumps(product)
            )
            self.logger.info(f"Create product status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))
            return None

    def update_product(
        self,
        productId,
        data,
    ):
        """
        Update a product with the given data.
        """
        endpoint = f"{self.base_url_v1}products/{productId}"
        try:
            response = requests.patch(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            self.logger.info(f"Update product status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))
            return None

    def update_variant(
        self,
        productId,
        variantId=None,
        choices=None,
        price=None,
        cost=None,
        sku=None,
        visible=None,
    ):
        endpoint = f"{self.base_url_v1}products/{productId}/variants"
        # Create the variant dictionary
        variant = {}
        if variantId is not None:
            variant["variantId"] = [variantId]

        # Add the optional fields to the variant dictionary
        if choices is not None:
            variant["choices"] = choices
        if price is not None:
            variant["price"] = price
        if cost is not None:
            variant["cost"] = cost
        if sku is not None:
            variant["sku"] = sku
        if visible is not None:
            variant["visible"] = visible
        data = {"variants": [variant]}
        try:
            response = requests.patch(
                endpoint, headers=self.headers, data=json.dumps(data)
            )
            self.logger.info(f"Update variant status code: {response.status_code}")
            return self._handle_response(response)
        except requests.RequestException as e:
            self.logger.error(str(e))
            return None


def main():
    ord = Orders()
    print(ord.site_id)
    # ask user for input
    order_id = input("Enter order id: ")
    pprint(ord.get_order(order_id))


if __name__ == "__main__":
    main()
