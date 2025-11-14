"""
Locust load testing for District Marketplace.

Tests the following scenarios:
1. Product listing (AI ingestion)
2. Product search (vector similarity)
3. Mixed workload (realistic usage)

Run with:
    locust -f load_tests/locustfile.py --host=http://localhost:8000

For web UI: http://localhost:8089
"""

from locust import HttpUser, task, between, events
import random
import json
import time
import os


# Sample product data for testing
SAMPLE_PRODUCTS = [
    "Fresh tomatoes 10 kg at 40 rupees per kg",
    "Samsung Galaxy S24 Ultra 256GB at 124999 rupees",
    "HP LaserJet Printer at 12000 rupees",
    "Basmati Rice 25 kg at 80 rupees per kg",
    "Leather Wallet at 899 rupees",
    "Nike Running Shoes size 10 at 4500 rupees",
    "iPhone 15 Pro 256GB at 134900 rupees",
    "Dell Laptop i5 8GB RAM at 55000 rupees",
    "Fresh Apples 5 kg at 120 rupees per kg",
    "Sony Headphones at 2500 rupees",
    "Organic Honey 1 kg at 600 rupees",
    "Wooden Chair at 3500 rupees",
    "Cotton T-Shirt XL at 499 rupees",
    "LED Bulbs pack of 10 at 800 rupees",
    "Cooking Oil 5 liters at 650 rupees per liter",
]

SAMPLE_SEARCH_QUERIES = [
    "mobile phone",
    "laptop",
    "vegetables",
    "rice",
    "shoes",
    "headphones",
    "fresh fruits",
    "furniture",
    "clothing",
    "electronics",
]


class MarketplaceUser(HttpUser):
    """
    Simulates a typical marketplace user.

    Users perform a mix of:
    - Product listings (sellers)
    - Product searches (buyers)
    - Browsing products
    """

    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts - setup initial state."""
        # Get CSRF token if needed
        self.client.get("/")

    @task(3)
    def list_product_text(self):
        """
        List a product using text input (extract + create).
        This is a common seller action.
        Weight: 3 (happens frequently)
        """
        product_text = random.choice(SAMPLE_PRODUCTS)

        # Step 1: Extract details
        start_time = time.time()
        extract_response = self.client.post(
            "/ingest/api/extract/",
            json={"text": product_text},
            headers={"Content-Type": "application/json"},
            name="/ingest/api/extract/ [Extract Product Details]"
        )

        if extract_response.status_code == 200:
            data = extract_response.json()
            if data.get('success'):
                extracted = data.get('extracted_data', {})

                # Step 2: Create product (simulate user accepting extracted data)
                create_data = {
                    "input_type": "text",
                    "text": product_text,
                    "product_name": extracted.get('name', 'Test Product'),
                    "product_description": extracted.get('description', ''),
                    "product_price": extracted.get('price', 100),
                    "product_quantity": extracted.get('quantity', 1),
                    "product_unit": extracted.get('unit', 'piece'),
                    "product_category": extracted.get('category', 'General'),
                    "selected_image_urls": []
                }

                create_response = self.client.post(
                    "/ingest/api/create/",
                    json=create_data,
                    headers={"Content-Type": "application/json"},
                    name="/ingest/api/create/ [Create Product]"
                )

                total_time = (time.time() - start_time) * 1000  # ms

                # Log performance metrics
                events.request.fire(
                    request_type="POST",
                    name="Full Product Listing Flow",
                    response_time=total_time,
                    response_length=len(create_response.content),
                    exception=None if create_response.status_code == 201 else Exception("Failed"),
                    context={}
                )

    @task(5)
    def search_products(self):
        """
        Search for products using text query.
        This is a common buyer action.
        Weight: 5 (happens most frequently)
        """
        query = random.choice(SAMPLE_SEARCH_QUERIES)

        search_data = {
            "query": query,
            "search_type": "text"
        }

        self.client.post(
            "/search/api/",
            json=search_data,
            headers={"Content-Type": "application/json"},
            name="/search/api/ [Search Products]"
        )

    @task(2)
    def browse_products(self):
        """
        Browse product list.
        Weight: 2 (moderate frequency)
        """
        self.client.get(
            "/products/api/",
            name="/products/api/ [Browse All Products]"
        )

    @task(1)
    def view_product_detail(self):
        """
        View a specific product detail.
        Weight: 1 (less frequent)
        """
        # Random product ID (1-100)
        product_id = random.randint(1, 100)
        self.client.get(
            f"/products/api/{product_id}/",
            name="/products/api/{id}/ [View Product Detail]"
        )


class SellerUser(HttpUser):
    """
    Simulates a seller who primarily lists products.
    Use this for testing product creation load specifically.
    """

    wait_time = between(2, 5)

    @task
    def list_product(self):
        """Sellers only list products."""
        product_text = random.choice(SAMPLE_PRODUCTS)

        # Extract + Create flow
        extract_response = self.client.post(
            "/ingest/api/extract/",
            json={"text": product_text},
            headers={"Content-Type": "application/json"}
        )

        if extract_response.status_code == 200:
            data = extract_response.json()
            if data.get('success'):
                extracted = data.get('extracted_data', {})

                create_data = {
                    "input_type": "text",
                    "text": product_text,
                    "product_name": extracted.get('name', 'Test Product'),
                    "product_description": extracted.get('description', ''),
                    "product_price": extracted.get('price', 100),
                    "product_quantity": extracted.get('quantity', 1),
                    "product_unit": extracted.get('unit', 'piece'),
                    "product_category": extracted.get('category', 'General'),
                }

                self.client.post(
                    "/ingest/api/create/",
                    json=create_data,
                    headers={"Content-Type": "application/json"}
                )


class BuyerUser(HttpUser):
    """
    Simulates a buyer who primarily searches and browses.
    Use this for testing search load specifically.
    """

    wait_time = between(1, 3)

    @task(5)
    def search_products(self):
        """Buyers search frequently."""
        query = random.choice(SAMPLE_SEARCH_QUERIES)

        self.client.post(
            "/search/api/",
            json={"query": query, "search_type": "text"},
            headers={"Content-Type": "application/json"}
        )

    @task(3)
    def browse_products(self):
        """Buyers browse product listings."""
        self.client.get("/products/api/")

    @task(2)
    def view_product(self):
        """Buyers view product details."""
        product_id = random.randint(1, 100)
        self.client.get(f"/products/api/{product_id}/")


# Custom event listeners for detailed metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "="*70)
    print("LOAD TEST STARTED")
    print("="*70)
    print(f"Host: {environment.host}")
    print(f"Using Mock AI: {os.getenv('USE_MOCK_AI', 'False')}")
    print("="*70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - print summary."""
    print("\n" + "="*70)
    print("LOAD TEST COMPLETED")
    print("="*70)

    stats = environment.stats

    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"RPS: {stats.total.total_rps:.2f}")

    print(f"\nResponse Times:")
    print(f"  Median: {stats.total.median_response_time:.0f} ms")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.0f} ms")
    print(f"  Average: {stats.total.avg_response_time:.0f} ms")
    print(f"  Max: {stats.total.max_response_time:.0f} ms")

    print("\n" + "="*70 + "\n")
