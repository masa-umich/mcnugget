# Import any http libraries you need to make a GET request to
# https://api.ni.com/e/mktg/product-catalog/1/en-us/category/digital-io?size=24&page=1&getPrice=false
# add the headers
# Client_id = 1fcca773908c4e6da0500a60ea393e83
# Client_secret = 9EC7AA4494614C25AE57f022Bc6f7Bac

# Path: scrape-ni.py

import requests
import json

url = "https://api.ni.com/e/mktg/product-catalog/1/en-us/category"

CATEGORIES = [
    "multifunction-io",
    "voltage",
    "current",
    "digital-io",
    "temperature",
    "compactdaq-chassis",
    # "compactdaq-controllers",
    "pxi-chassis",
    "pxi-controllers"
]

headers = {
    "Client_id": "1fcca773908c4e6da0500a60ea393e83",
    "Client_secret": "9EC7AA4494614C25AE57f022Bc6f7Bac"
}

# For each category, make a GET request to the API
# and print it as json

COUNT = 0

products = []


def check_has_property(product, property):
    for item in product["productData"]:
        if item["id"] == property:
            return True
    return False


for category in CATEGORIES:
    response = requests.get(url + "/" + category, headers=headers)
    n_pages = response.json()["pagination"]["totalPages"]
    for page in range(1, n_pages + 1):
        print("Category: " + category + " Page: " + str(page))
        response = requests.get(url + "/" + category + "?&page=" + str(page) + "&getPrice=false", headers=headers)
        j = response.json()
        l_products = j["products"]
        COUNT += len(j["products"])
        for product in l_products:
            for key in list(product.keys()):
                if key not in ["id", "tileLabel", "productID", "productData", "productSpecs"]:
                    del product[key]
            product["category"] = category
            if "Bundle" not in product["tileLabel"]:
                products.append(product)

                if category == "pxi-chassis" or category == "compactdaq-chassis":
                    # check that it has the "SlotCount" property in the productData
                    if not check_has_property(product, "SlotCount"):
                        print(f"Product {product['tileLabel']} does not have SlotCount")

                if category == "voltage":
                    if not check_has_property(product, "AnalogInputChannels"):
                        print(f"Product {product['tileLabel']} does not have AnalogInputChannels")

print(len(products))
print(COUNT)
# check if there are any duplicates
for product in products:
    specs_url = product["productSpecs"]
    if "search" not in specs_url and "specs.html" in specs_url:
        specs_url = specs_url[specs_url.find("bundle") + 7:]
        print(specs_url)
        base_url = "https://docs-be.ni.com/api/bundle/"
        response = requests.get(base_url + specs_url, headers=headers)
        print(response.json()["metadata"]["DocumentID"])

# dump the products JSON file
with open("products.json", "w") as f:
    json.dump(products, f)

# %%
