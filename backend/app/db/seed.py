import asyncio
import os
import httpx

API_URL = os.getenv("RANKFORGE_API_URL", "http://localhost:8000")

SAMPLE_PRODUCTS = [
    {"sku": "GROC-ATTA-01", "title": "Aashirvaad Shudh Chakki Whole Wheat Flour 5kg", "description": "100% MP sharbati whole wheat chakki atta for soft rotis and chapatis", "brand": "Aashirvaad", "category": "Groceries", "price_inr": 265, "rating": 4.6, "stock_qty": 120},
    {"sku": "GROC-ATTA-02", "title": "Fortune Chakki Fresh Atta 10kg", "description": "Freshly milled whole wheat flour rich in dietary fiber for daily Indian cooking", "brand": "Fortune", "category": "Groceries", "price_inr": 445, "rating": 4.4, "stock_qty": 85},
    {"sku": "ELEC-PHN-01", "title": "Apple iPhone 15 128GB Black", "description": "6.1-inch Super Retina XDR display, A16 Bionic chip, 48MP main camera, USB-C", "brand": "Apple", "category": "Smartphones", "price_inr": 65999, "rating": 4.7, "stock_qty": 30},
    {"sku": "ELEC-PHN-02", "title": "Samsung Galaxy S24 5G 256GB Onyx Black", "description": "Dynamic AMOLED 2X 120Hz display, Galaxy AI features, pro-grade triple camera", "brand": "Samsung", "category": "Smartphones", "price_inr": 74999, "rating": 4.6, "stock_qty": 25},
    {"sku": "ELEC-KBD-01", "title": "Keychron K2 Pro Wireless Mechanical Keyboard Silent Red Switches", "description": "Low-noise damped tactile typing experience ideal for quiet office desks and coding", "brand": "Keychron", "category": "Computer Accessories", "price_inr": 9499, "rating": 4.8, "stock_qty": 18},
    {"sku": "ELEC-KBD-02", "title": "Logitech MX Keys S Illuminated Wireless Keyboard", "description": "Whisper-quiet low-profile scissor keys built for productivity and long programming sessions", "brand": "Logitech", "category": "Computer Accessories", "price_inr": 10995, "rating": 4.7, "stock_qty": 40},
    {"sku": "ELEC-AUD-01", "title": "Sony WH-1000XM5 Wireless Active Noise Cancelling Headphones", "description": "Industry-leading ANC over-ear headphones with 30-hour battery and multipoint Bluetooth", "brand": "Sony", "category": "Audio", "price_inr": 26990, "rating": 4.8, "stock_qty": 15},
    {"sku": "ELEC-AUD-02", "title": "OnePlus Buds 3 TWS Earphones", "description": "49dB adaptive noise cancellation wireless earbuds with dual dynamic drivers and fast charging", "brand": "OnePlus", "category": "Audio", "price_inr": 5499, "rating": 4.5, "stock_qty": 65},
    {"sku": "HOME-MIX-01", "title": "Preethi Zodiac MG-218 750W Mixer Grinder", "description": "Heavy duty 750 watt Vega W5 motor with Master Chef food processor jar for Indian spices and chutneys", "brand": "Preethi", "category": "Home Appliances", "price_inr": 8499, "rating": 4.5, "stock_qty": 22},
    {"sku": "FOOT-SLP-01", "title": "Puma Leadcat 2.0 Cushioned Men's Slides", "description": "Lightweight EVA cushioned casual slippers and flip flops for indoor and outdoor daily wear", "brand": "Puma", "category": "Footwear", "price_inr": 1499, "rating": 4.3, "stock_qty": 90},
]


async def seed():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{API_URL}/v1/products/bulk",
            headers={"X-API-Key": "rf_admin_dev_key"},
            json=SAMPLE_PRODUCTS,
        )
        resp.raise_for_status()
        print("Seed response:", resp.json())


if __name__ == "__main__":
    asyncio.run(seed())
