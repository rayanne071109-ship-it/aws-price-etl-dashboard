import requests
import csv

API_KEY = "AIzaSyCpl5xc4SZ3WtzGmYSuBCRbcn60Q-oKPfE"
BASE_URL = "https://cloudbilling.googleapis.com/v1/services"

# Lista serviços disponíveis
services = requests.get(f"{BASE_URL}?key={API_KEY}").json()

with open("gcp_prices.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Service", "SKU", "Description", "Pricing"])

    for service in services.get("services", []):
        service_id = service["name"].split("/")[-1]
        skus_url = f"{BASE_URL}/{service_id}/skus?key={API_KEY}"
        skus = requests.get(skus_url).json()
        
        for sku in skus.get("skus", []):
            pricing = sku.get("pricingInfo", [])
            writer.writerow([
                service["displayName"],
                sku["name"],
                sku["description"],
                pricing
            ])
