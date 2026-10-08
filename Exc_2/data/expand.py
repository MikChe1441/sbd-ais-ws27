import csv
import random

NUM_ROWS = 1_000_000
OUTPUT_FILE = "people_1M.csv"
random.seed(42)

# -------------------------
# FIRST NAMES (100+ each)
# -------------------------

FIRST_NAMES_FEMALE = [
    "Alice","Anna","Amelia","Ava","Beatrice","Camila","Carla","Charlotte",
    "Clara","Daniela","Diana","Elena","Ella","Emily","Emma","Eva","Fatima",
    "Francesca","Gabriela","Grace","Hannah","Helena","Ines","Irene","Isabella",
    "Julia","Katarina","Laura","Lea","Lina","Lucia","Marta","Maria","Marina",
    "Maya","Mila","Nadia","Natalia","Nina","Olivia","Paula","Petra","Rosa",
    "Sara","Sofia","Sophia","Teresa","Valentina","Vera","Victoria","Yara",
    "Zoe","Noemi","Elsa","Ivy","Layla","Bianca","Chiara","Anita","Monica",
    "Renata","Simone","Alexandra","Silvia","Patricia","Angela","Iris",
    "Jasmine","Nora","Carmen","Raquel","Miriam","Daniela","Juliana","Rita",
    "Adriana","Lara","Tania","Veronica","Mariana","Tatiana","Alina","Oksana",
    "Irina","Svetlana","Ksenia","Anastasia","Polina","Yulia"
]

FIRST_NAMES_MALE = [
    "Adam","Adrian","Alexander","Andreas","Anthony","Antonio","Benjamin",
    "Bruno","Carlos","Christian","Daniel","David","Diego","Dominik","Eduardo",
    "Elias","Eric","Felix","Fernando","Francisco","Gabriel","George","Gianni",
    "Hector","Henry","Hugo","Ivan","Jack","James","Jan","Javier","Joao",
    "John","Jonas","Jose","Julian","Karim","Kevin","Lars","Leo","Leon",
    "Luca","Lucas","Luis","Marco","Martin","Mateo","Matthias","Max","Michael",
    "Miguel","Mohamed","Nicolas","Noah","Oliver","Oscar","Pablo","Patrick",
    "Paul","Pedro","Rafael","Ricardo","Robert","Roman","Samuel","Sebastian",
    "Sergio","Stefan","Thomas","Tim","Tobias","Victor","Viktor","William",
    "Yusuf","Zoran","Andrei","Bogdan","Milan","Filip","Omar","Ali","Emir"
]

# -------------------------
# LAST NAMES (100+)
# -------------------------

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Miller","Davis","Garcia",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
    "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell",
    "Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz","Parker",
    "Cruz","Edwards","Collins","Reyes","Stewart","Morris","Morales","Murphy",
    "Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper","Peterson",
    "Baumann","Schmidt","Muller","Weber","Fischer","Huber","Gruber",
    "Kowalski","Nowak","Novak","Horvat","Popescu","Ionescu","Petrov",
    "Ivanov","Smirnov","Kovac","Markovic","Jensen","Hansen","Larsen"
]

# -------------------------
# DEPARTMENTS (100+)
# -------------------------

BASE_DEPARTMENTS = [
    "Engineering","Marketing","Finance","HR","Sales","IT","Operations",
    "Security","Compliance","Legal","Data Science","Machine Learning",
    "Cloud Infrastructure","DevOps","SRE","QA","Product Management",
    "UX Design","UI Design","Customer Support","Customer Success",
    "Business Intelligence","Analytics","Research","Innovation",
    "Supply Chain","Procurement","Logistics","Manufacturing",
    "Quality Assurance","Risk Management","Audit","Treasury",
    "Tax","Accounting","Payroll","Internal Tools","Platform",
    "Mobile Development","Web Development","Backend","Frontend",
    "API","Integration","Middleware","Observability","Monitoring",
    "Incident Response","SOC","IAM","GRC","Fraud Detection",
    "Payments","Billing","Subscriptions","Pricing","Growth",
    "SEO","Content","Brand","Communications","Public Relations",
    "Investor Relations","Corporate Strategy","M&A","Partnerships",
    "Alliances","Training","Learning & Development","People Analytics",
    "Workforce Planning","Facilities","Real Estate","Sustainability",
    "ESG","Energy Management","Health & Safety","Regulatory Affairs",
    "Clinical Operations","Bioinformatics","Pharmacovigilance",
    "Game Design","Game Analytics","Level Design","Community Management"
]

# salary ranges per department category
DEPARTMENT_SALARY = {
    "default": (60000, 110000),
    "Engineering": (80000, 150000),
    "Data": (85000, 160000),
    "Executive": (120000, 250000),
    "Support": (50000, 90000)
}

# -------------------------
# COUNTRIES (100+)
# -------------------------

COUNTRIES = [
    "USA","Canada","Mexico","Brazil","Argentina","Chile","Peru","Colombia",
    "UK","Ireland","France","Germany","Netherlands","Belgium","Spain","Portugal",
    "Italy","Switzerland","Austria","Poland","Czech Republic","Slovakia",
    "Hungary","Romania","Bulgaria","Croatia","Slovenia","Serbia","Bosnia",
    "Greece","Turkey","Norway","Sweden","Finland","Denmark","Iceland",
    "Estonia","Latvia","Lithuania","Ukraine","Moldova","Georgia","Armenia",
    "Russia","Kazakhstan","Uzbekistan","India","Pakistan","Bangladesh",
    "Sri Lanka","Nepal","China","Japan","South Korea","Taiwan","Hong Kong",
    "Singapore","Malaysia","Thailand","Vietnam","Indonesia","Philippines",
    "Australia","New Zealand","South Africa","Nigeria","Kenya","Ghana",
    "Egypt","Morocco","Tunisia","Algeria","Israel","Jordan","Lebanon",
    "Saudi Arabia","UAE","Qatar","Kuwait","Oman","Iran","Iraq","Syria",
    "Chile","Bolivia","Paraguay","Uruguay","Panama","Costa Rica","Cuba",
    "Dominican Republic","Jamaica","Trinidad and Tobago"
]

# -------------------------
# DATA GENERATOR
# -------------------------

def random_salary(department):
    if "Engineering" in department or "Platform" in department:
        low, high = DEPARTMENT_SALARY["Engineering"]
    elif "Data" in department or "Analytics" in department:
        low, high = DEPARTMENT_SALARY["Data"]
    elif "Support" in department or "Customer" in department:
        low, high = DEPARTMENT_SALARY["Support"]
    else:
        low, high = DEPARTMENT_SALARY["default"]
    return random.randint(low, high)

def random_person():
    gender = random.choice(["Male", "Female"])

    first_name = (
        random.choice(FIRST_NAMES_MALE)
        if gender == "Male"
        else random.choice(FIRST_NAMES_FEMALE)
    )

    last_name = random.choice(LAST_NAMES)
    department = random.choice(BASE_DEPARTMENTS)
    country = random.choice(COUNTRIES)
    salary = random_salary(department)

    return [
        first_name,
        last_name,
        gender,
        department,
        salary,
        country
    ]

# -------------------------
# CSV WRITING (STREAMING)
# -------------------------

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "first_name","last_name","gender",
        "department","salary","country"
    ])

    for _ in range(NUM_ROWS):
        writer.writerow(random_person())

print(f"Generated {NUM_ROWS:,} rows -> {OUTPUT_FILE}")
