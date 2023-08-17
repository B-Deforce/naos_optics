import sys
import os

sys.path.append("..")

from wix_api import Products, Orders, Inventory
from utils import sku_replace, setup_logger, send_email
import logging
from pprint import pprint


class StockManager:
    def __init__(self):
        self.sku_replace = sku_replace
        self.ord = Orders()
        self.sg_api_key = os.getenv("SG_API_KEY")
        assert self.sg_api_key, "Sendgrid API key not found"
        self.logger = setup_logger("stck_mngr", "../logs/stck_mngr.log")

    def get_order_details(self, orderId):
        try:
            order = self.ord.get_order(orderId)
            name_details = (
                order["order"]["buyerInfo"]["firstName"],
                order["order"]["buyerInfo"]["lastName"],
            )
            order_stock_details = []
            for i in order["order"]["lineItems"]:
                if i["lineItemType"] != "PHYSICAL":
                    self.logger.info(
                        i["name"]
                        + " is not a physical product, so this will not be processed"
                    )
                else:
                    order_stock_details.append((i["sku"], i["quantity"]))
            return name_details, order_stock_details
        except Exception as e:
            self.logger.error(
                f"Error getting SKU and quantity for order {orderId}: {str(e)}"
            )

    def prep_inventory_email(
        self, orderId, product_details, name_details, status, update_status_idx=None
    ):
        """
        Prepares the email to be sent for the inventory update status.
        """
        message = f"Order {orderId} was processed with status {status}.\n"
        message += f"Order details:\n"
        message += f"Name: {name_details[0]} {name_details[1]}\n"
        message += f"Products:\n"
        for product, quantity in product_details:
            message += f"{product[0]}: -{quantity} ({product[-1]})\n"
        if update_status_idx is not None:
            message += f"Failed to update inventory for the following products:\n"
            for idx in update_status_idx:
                message += f"{product_details[idx][0][0]}: {product_details[idx][1]}\n"
        subject = (
            f"[{status}] Inventory Update Status - {name_details[0]} {name_details[1]}"
        )
        return message, subject


class SKUHandler(StockManager):
    def __init__(self):
        super().__init__()
        self.prod = Products()
        self.sku_mapping = {}
        self._build_sku_mapping()

    def _build_sku_mapping(self):
        try:
            # get all products
            products = self.prod.query_products(
                includeVariants=True, includeHiddenProducts=True
            )
            i = 0
            for product in products["products"]:
                if product["manageVariants"] == True:
                    for variant in product["variants"]:
                        if "-" not in variant["variant"]["sku"]:
                            self.sku_mapping[variant["variant"]["sku"]] = (
                                product["name"],
                                product["id"],
                                variant["id"],
                                variant["choices"],
                            )
                elif (
                    ("sku" in product)
                    & (product["sku"] != "")
                    & ("-" not in product["sku"])
                ):
                    self.sku_mapping[product["sku"]] = (
                        product["name"],
                        product["id"],
                        None,
                        None,
                    )
                else:
                    self.logger.warning(f"product {product['name']} has no sku")
        except Exception as e:
            self.logger.error(f"Error getting SKU mapping: {str(e)}")

    def process_sku(self, sku):
        if sku in self.sku_mapping:
            return self.sku_mapping[sku]
        elif sku in self.sku_replace.keys():
            return self.sku_mapping[self.sku_replace[sku]]
        else:
            self.logger.error(f"Sku {sku} not found in  sku mapping")


def main():
    sku_handler = SKUHandler()
    sm = StockManager()
    inv = Inventory()
    order_id = input("Enter order id: ")
    name_details, order_stock_details = sm.get_order_details(order_id)
    if order_stock_details is None:
        sm.logger.error(f"failed to get details for order {order_id}")
    product_details = []
    for concat_sku, quantity in order_stock_details:
        sku_parts = concat_sku.split("-")
        for sku in sku_parts:
            product = sku_handler.process_sku(sku)
            if product is None:
                sm.logger.error(f"failed to get product details for sku {sku}")
                continue
            product_details.append((product, quantity))
    update_status_idx = []
    i = 0
    for product, quantity in product_details:
        productid, variantid = product[1], product[2]
        response = inv.decrease_inventory(productid, variantid, quantity)
        if response.status_code == 200:
            sm.logger.info(f"Successfully updated inventory for product {productid}")
        else:
            update_status_idx.append(i)
            i += 1
            logging.error(
                f"Failed to update inventory for product {productid} with status code {response.status_code}"
            )
    if len(update_status_idx) == 0:
        msg, sub = sm.prep_inventory_email(
            order_id, product_details, name_details, status="SUCCESS"
        )
        send_email(
            msg,
            sub,
            "info@naos-optics.com",  # public facing email
            "info@naos-optics.com",  # public facing email
            sm.sg_api_key,
            sm.logger,
        )
    else:
        msg, sub = sm.prep_inventory_email(
            order_id,
            product_details,
            name_details,
            status="FAIL",
            update_status_idx=update_status_idx,
        )
        send_email(
            msg,
            sub,
            "info@naos-optics.com",  # public facing email
            "info@naos-optics.com",  # public facing email
            sm.sg_api_key,
            sm.logger,
        )


if __name__ == "__main__":
    main()
