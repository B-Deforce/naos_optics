from src.wix_api import Products
from pprint import pprint
import pandas as pd
from src.utils import send_email
import os

def main():
    df = pd.DataFrame(columns=['Product Name', 'Variant', 'Stock'])
    mail = ""
    prod = Products()
    products = prod.query_products(includeVariants=True, includeHiddenProducts=True)
    for product in products["products"]:
        if product["stock"]["trackInventory"] == True:
            if product["manageVariants"] == True:
                for variant in product["variants"]:
                    if variant["variant"]["sku"] != '':
                        df = pd.concat([df, pd.DataFrame({'Product Name': [product["name"]], 'Variant': ["-".join(variant["choices"].values())], 'Stock': [variant["stock"]["quantity"]]}, columns=['Product Name', 'Variant', 'Stock'])], ignore_index=True)
                        if (variant["stock"]["quantity"] < 10) & (variant["stock"]["quantity"] > 0):
                            mail += f"<p>The product {product['name']} - {variant['variant']['sku']} is low in stock. Quantity: {variant['stock']['quantity']}</p>"
                        elif variant["stock"]["quantity"] == 0:
                            mail += f"<p><strong><font color='red'>The product {product['name']} - {variant['variant']['sku']} is out of stock.</font></strong></p>"
            else:
                df = pd.concat([df, pd.DataFrame({'Product Name': [product["name"]], 'Variant': [''], 'Stock': [product["stock"]["quantity"]]}, columns=['Product Name', 'Variant', 'Stock'])], ignore_index=True)
                if (product["stock"]["quantity"] < 10) & (product["stock"]["quantity"] > 0):
                    mail += f"<p>The product {product['name']} is low in stock. Quantity: {product['stock']['quantity']}</p>"
                elif product["stock"]["quantity"] == 0:
                    mail += f"<p><strong><font color='red'>The product {product['name']} is out of stock.</font></strong></p>"
    df.to_csv('stock.csv', index=False)
    send_email(mail, "Stock Report", "info@naos-optics.com", "info@naos-optics.com", os.getenv("SG_API_KEY"), attachment='stock.csv', filetype='text/csv')
    print("mail sent")
if __name__ == '__main__':
    main()