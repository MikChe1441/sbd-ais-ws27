import csv
import random
from datetime import datetime, timedelta

# -------------------------
# CONFIGURATION
# -------------------------
NUM_ROWS = 1_000_000
OUTPUT_FILE = "../data/orders_1M.csv"  # written into ./data, which is mounted at /data in the postgres container
SEED = 42  # fixed seed for reproducibility
random.seed(SEED)

# -------------------------
# CUSTOMER NAMES
# -------------------------
FIRST_NAMES = [
    "Alice","Bob","Carol","David","Eve","Frank","Grace","Henry",
    "Ivy","John","Liam","Mia","Noah","Olivia","Emma","Sophia",
    "James","Lucas","Amelia","Charlotte","Amir","Sara","Nina",
    "Leo","Maya","Ethan","Lara","Victor","Zoe","Anna","Daniel","Julia"
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Miller","Davis",
    "Garcia","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez",
    "Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark",
    "Ramirez","Lewis","Robinson","Walker","Young","Allen"
]

# -------------------------
# PRODUCT CATEGORIES & PRICE RANGES
# -------------------------
PRODUCT_CATEGORIES = [
    "Electronics","Fashion","Home & Garden","Sports","Toys",
    "Books","Health & Beauty","Automotive","Grocery","Office Supplies"
]

CATEGORY_PRICE = {
    "Electronics": (100, 1500),
    "Fashion": (10, 200),
    "Home & Garden": (20, 500),
    "Sports": (15, 400),
    "Toys": (5, 150),
    "Books": (5, 80),
    "Health & Beauty": (10, 300),
    "Automotive": (50, 2000),
    "Grocery": (2, 100),
    "Office Supplies": (5, 250)
}

# -------------------------
# COUNTRIES
# -------------------------
COUNTRIES = [
    "USA","Canada","UK","Germany","France","Spain","Italy","Netherlands",
    "Sweden","Australia","Brazil","Mexico","India","Japan","China"
]

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def random_date(start_year=2024, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).date()

def random_customer_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_price(category):
    low, high = CATEGORY_PRICE.get(category, (10, 500))
    return round(random.uniform(low, high), 2)

def random_order():
    category = random.choice(PRODUCT_CATEGORIES)
    quantity = random.randint(1, 5)
    return [
        random_customer_name(),
        category,
        quantity,
        random_price(category),
        random_date(),
        random.choice(COUNTRIES)
    ]

# -------------------------
# CSV GENERATION
# -------------------------
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "customer_name","product_category","quantity",
        "price_per_unit","order_date","country"
    ])
    
    for _ in range(NUM_ROWS):
        writer.writerow(random_order())

print(f"Generated {NUM_ROWS:,} rows -> {OUTPUT_FILE}")
