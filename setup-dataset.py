#!/usr/bin/env python3
'''
INK Platform Database Setup Script for Christ University

This script sets up the MongoDB database for the INK platform with all collections
and populates them with realistic sample data focusing on Christ University students.

To run:
1. Make sure MongoDB is running locally
2. Run: python setup_database.py
'''

from pymongo import MongoClient, IndexModel, ASCENDING, DESCENDING, GEO2D
from datetime import datetime, timedelta
import random
import string
import uuid
import names  # You may need to pip install names
import json
from bson import ObjectId
import pprint

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['ink_database']

# Track generated names to avoid duplicates
generated_subreddit_names = set()
generated_usernames = set()

# Helper function to format ObjectId as string for pretty printing
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

def print_json(data):
    print(json.dumps(data, indent=2, cls=JSONEncoder))

# Clear existing collections if they exist (for testing)
def reset_database():
    print("Clearing existing collections...")
    collections = [
        'users', 'widgets', 'bounties', 'bounty_responses', 'bounty_votes',
        'marketplace_listings', 'marketplace_transactions', 'subreddits',
        'threads', 'comments', 'study_spots', 'occupancy_reports', 'check_ins',
        'tutor_profiles', 'tutoring_sessions', 'tutor_reviews',
        'coin_transactions', 'conversations', 'messages'
    ]
    for collection in collections:
        if collection in db.list_collection_names():
            db[collection].drop()
    print("Database reset complete.")

# Sample data generators
def get_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def get_random_time(start_hour=8, end_hour=22):
    """Generate a random time between start_hour and end_hour"""
    hour = random.randint(start_hour, end_hour)
    minute = random.choice([0, 15, 30, 45])
    return hour, minute

def get_random_university():
    # Focus on Christ University and related campuses
    universities = [
        "Christ University Main Campus", "Christ University Kengeri Campus", 
        "Christ University Bannerghatta Road Campus", "Christ University Yeshwanthpur Campus",
        "Christ University Delhi NCR Campus", "Christ University Lavasa Campus",
        "Christ University School of Business and Management", "Christ University School of Law"
    ]
    return random.choice(universities)

def get_random_department():
    # Enhanced department list with Christ University specific departments
    departments = [
        "Computer Science", "Data Science", "Artificial Intelligence", "Machine Learning",
        "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", 
        "Physics", "Mathematics", "Biology", "Chemistry", "Biotechnology", "Microbiology",
        "Business Administration", "Economics", "Finance", "Marketing", "Human Resources",
        "Psychology", "English Literature", "History", "Political Science", "Sociology",
        "Mass Communication", "Journalism", "Media Studies", "Film Studies", "Animation",
        "Medicine", "Nursing", "Pharmacy", "Law", "Education", "Music", "Dance", "Theatre",
        "Hotel Management", "Tourism", "Fashion Design", "Interior Design", "Architecture"
    ]
    return random.choice(departments)

def get_random_year():
    years = ["1st Year", "2nd Year", "3rd Year", "Final Year", "Masters", "PhD", "Post-Doctoral"]
    return random.choice(years)

def get_random_skills(department):
    """Generate relevant skills based on department"""
    skill_sets = {
        "Computer Science": ["Python", "Java", "C++", "JavaScript", "Web Development", "Algorithms", "Data Structures", "Machine Learning", "AI", "Cloud Computing", "Cybersecurity", "DevOps", "Mobile App Development", "Database Design", "Software Engineering"],
        "Data Science": ["Python", "R", "SQL", "Statistics", "Data Visualization", "Machine Learning", "Big Data", "Data Mining", "Tableau", "Pandas", "NumPy", "SciPy", "TensorFlow", "Hadoop", "Spark"],
        "Artificial Intelligence": ["Machine Learning", "Deep Learning", "Neural Networks", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "Reinforcement Learning", "Genetic Algorithms", "Fuzzy Logic", "Expert Systems"],
        "Machine Learning": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Neural Networks", "SVM", "Decision Trees", "Random Forest", "Gradient Boosting", "Feature Engineering", "Model Evaluation"],
        "Electrical Engineering": ["Circuit Design", "Microcontrollers", "Signal Processing", "MATLAB", "PCB Design", "Embedded Systems", "Power Systems", "Control Systems", "Robotics", "IoT", "PLC Programming"],
        "Mechanical Engineering": ["CAD", "FEA", "Thermodynamics", "Fluid Mechanics", "SolidWorks", "MATLAB", "3D Printing", "Materials Science", "Stress Analysis", "Mechatronics", "Robotics", "Manufacturing Processes"],
        "Civil Engineering": ["Structural Analysis", "AutoCAD", "Building Information Modeling", "Geotechnical Engineering", "Highway Design", "Environmental Engineering", "Construction Management", "Surveying", "Water Resources"],
        "Physics": ["MATLAB", "Data Analysis", "Quantum Mechanics", "Electromagnetism", "Thermodynamics", "Experimental Physics", "Python", "LaTeX", "Optics", "Nuclear Physics", "Astrophysics", "Computational Physics"],
        "Mathematics": ["Calculus", "Linear Algebra", "Probability", "Statistics", "MATLAB", "Python", "LaTeX", "Discrete Mathematics", "Numerical Analysis", "Differential Equations", "Graph Theory", "Operations Research"],
        "Biology": ["Microbiology", "Genetics", "Cell Biology", "Biochemistry", "Laboratory Techniques", "Data Analysis", "R", "CRISPR", "PCR", "Cell Culture", "Microscopy", "Bioinformatics"],
        "Chemistry": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", "Analytical Chemistry", "Laboratory Techniques", "Spectroscopy", "Chromatography", "Synthesis", "Catalysis", "Polymer Chemistry"],
        "Business Administration": ["Marketing", "Finance", "Accounting", "Management", "Business Strategy", "Excel", "Data Analysis", "Project Management", "Business Communication", "Leadership", "Entrepreneurship", "Digital Marketing"],
        "Economics": ["Microeconomics", "Macroeconomics", "Econometrics", "Statistical Analysis", "R", "STATA", "Game Theory", "Financial Analysis", "Economic Policy", "Development Economics", "International Trade"],
        "Finance": ["Financial Analysis", "Financial Modeling", "Investment Analysis", "Corporate Finance", "Portfolio Management", "Risk Management", "Excel", "Bloomberg Terminal", "Accounting", "Valuation"],
        "Marketing": ["Market Research", "Digital Marketing", "Social Media Marketing", "Brand Management", "Consumer Behavior", "SEO", "Content Marketing", "Marketing Analytics", "Product Development", "PR Management"],
        "Psychology": ["Research Methods", "Statistics", "Experimental Psychology", "Cognitive Psychology", "Clinical Psychology", "SPSS", "Survey Design", "Psychometrics", "Counseling", "Mental Health Assessment"],
        "English Literature": ["Creative Writing", "Literary Analysis", "Editing", "Research", "Critical Thinking", "Teaching", "Public Speaking", "Comparative Literature", "Cultural Studies", "Linguistics"],
        "History": ["Research", "Critical Analysis", "Writing", "Historiography", "Archival Research", "Teaching", "Documentation", "Archaeology", "Cultural Studies", "Political History"],
        "Political Science": ["Political Theory", "International Relations", "Policy Analysis", "Research Methods", "Public Speaking", "Statistical Analysis", "Geopolitics", "Diplomacy", "Public Administration"],
        "Medicine": ["Anatomy", "Physiology", "Biochemistry", "Pharmacology", "Clinical Skills", "Research Methods", "Patient Care", "Diagnostics", "Medical Ethics", "Emergency Medicine"],
        "Law": ["Legal Research", "Legal Writing", "Constitutional Law", "Criminal Law", "Civil Law", "Corporate Law", "International Law", "Legal Ethics", "Arbitration", "Trial Advocacy"],
        "Mass Communication": ["Journalism", "Media Production", "Public Relations", "Digital Media", "Storytelling", "Social Media Management", "Video Production", "Audio Editing", "Content Creation"],
        "Fashion Design": ["Sketching", "Pattern Making", "Textile Knowledge", "CAD", "Fashion Illustration", "Garment Construction", "Trend Analysis", "Portfolio Development", "Fashion Marketing"],
        "Hotel Management": ["Guest Relations", "Food & Beverage Management", "Event Planning", "Hospitality Marketing", "Revenue Management", "Kitchen Operations", "Customer Service", "Hotel Software Systems"]
    }
    
    # Get default skills if department not in skill_sets
    skills = skill_sets.get(department, ["Research", "Communication", "Critical Thinking", "Problem Solving", "Teamwork", "Time Management", "Project Management", "Microsoft Office"])
    
    # Return random subset of skills (3-8 skills)
    return random.sample(skills, random.randint(3, min(8, len(skills))))

def get_random_interests():
    interests = [
        "Machine Learning", "Web Development", "Mobile App Development", "Cybersecurity",
        "Blockchain", "Data Science", "Artificial Intelligence", "Robotics",
        "IoT", "Cloud Computing", "Game Development", "UI/UX Design",
        "Photography", "Music", "Art", "Sports", "Fitness", "Travel",
        "Reading", "Writing", "Cooking", "Gardening", "Hiking", "Swimming",
        "Chess", "Puzzle Solving", "Creative Writing", "Debate", "Astronomy",
        "Environmental Science", "Economics", "Finance", "Marketing", "Psychology",
        "Film Making", "Animation", "Graphic Design", "Public Speaking", "Volunteering",
        "Entrepreneurship", "Startups", "Social Media", "Content Creation", "Blogging",
        "Podcasting", "Event Management", "Fashion", "Interior Design", "Architecture",
        "History", "Philosophy", "Politics", "Stock Market", "Investing", "Yoga",
        "Meditation", "Mental Health", "Nutrition", "Dance", "Theatre", "Painting",
        "Sculpting", "Singing", "Playing Musical Instruments", "Cricket", "Football",
        "Basketball", "Athletics", "Badminton", "Table Tennis", "Cycling", "Running"
    ]
    return random.sample(interests, random.randint(3, 8))

def generate_firebase_uid():
    return f"firebase_{uuid.uuid4().hex[:20]}"

def generate_username(first_name, last_name):
    """Generate a unique username based on first and last name"""
    global generated_usernames
    
    base = f"{first_name.lower()}.{last_name.lower()}"
    username = base
    attempts = 0
    
    # Add random number if username already exists
    while username in generated_usernames:
        username = f"{base}{random.randint(1, 999)}"
        attempts += 1
        if attempts > 50:  # Avoid infinite loops
            username = f"{base}_{uuid.uuid4().hex[:6]}"
            break
    
    generated_usernames.add(username)
    return username

def generate_christ_user_sample():
    """Generate a sample user document for Christ University"""
    # 70% Indian names, 30% international names
    if random.random() < 0.7:
        # Indian names
        indian_first_names = [
            "Aditya", "Arjun", "Arnav", "Aryan", "Ayush", "Dhruv", "Ishaan", "Kabir",
            "Krishna", "Mohit", "Pranav", "Rahul", "Raj", "Rohan", "Vihaan", "Vivaan",
            "Aanya", "Aisha", "Ananya", "Avni", "Diya", "Ishita", "Kiara", "Meera",
            "Myra", "Nisha", "Pari", "Riya", "Saanvi", "Siya", "Trisha", "Zara",
            "Akshay", "Aman", "Ankit", "Chirag", "Darshan", "Deepak", "Harish", "Karan",
            "Mayank", "Nikhil", "Prakash", "Rakesh", "Sanjay", "Vijay", "Vishal", "Yash",
            "Anjali", "Deepika", "Divya", "Kavita", "Manisha", "Neha", "Pooja", "Priya",
            "Rekha", "Rina", "Shruti", "Sneha", "Sunita", "Swati", "Tanvi", "Uma"
        ]
        
        indian_last_names = [
            "Agarwal", "Bansal", "Bhat", "Choudhary", "Desai", "Gupta", "Jain", "Kumar",
            "Mehta", "Nair", "Patel", "Reddy", "Sharma", "Singh", "Verma", "Yadav",
            "Ahuja", "Bakshi", "Chopra", "Deshpande", "Goel", "Iyer", "Johar", "Kapoor",
            "Malhotra", "Naidu", "Pillai", "Rao", "Saxena", "Tiwari", "Wadhwa", "Zacharia",
            "Anand", "Biswas", "Chakraborty", "Das", "Gandhi", "Hegde", "Joshi", "Khanna",
            "Mishra", "Nayak", "Prasad", "Rajan", "Sen", "Thakur", "Venkatesh", "Walia"
        ]
        
        first_name = random.choice(indian_first_names)
        last_name = random.choice(indian_last_names)
    else:
        # International names
        first_name = names.get_first_name()
        last_name = names.get_last_name()
    
    username = generate_username(first_name, last_name)
    email = f"{username}@example.com"
    
    department = get_random_department()
    
    user = {
        "_id": ObjectId(),
        "firebase_uid": generate_firebase_uid(),
        "username": username,
        "email": email,
        "university": get_random_university(),
        "department": department,
        "year": get_random_year(),
        "skills": get_random_skills(department),
        "interests": get_random_interests(),
        "github_username": f"{username}_github" if random.random() > 0.3 else None,
        "github_url": f"https://github.com/{username}_github" if random.random() > 0.3 else None,
        "avatar_id": f"avatar{random.randint(1, 18)}",  # Expanded avatar range
        "auth_method": random.choice(["email_password", "google", "github"]),
        "onboarded": True,
        "created_at": get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31)),
        "coins_balance": random.randint(50, 5000)
    }
    
    return user

def generate_widget_sample(user_id):
    """Generate a sample widget document"""
    widget_types = ["profile", "skills", "github", "clock", "date", "notes", 
                    "spotify", "bounty", "marketplace", "studyspot"]
    widget_type = random.choice(widget_types)
    
    widget = {
        "_id": ObjectId(),
        "user_id": str(user_id),
        "widget_type": widget_type,
        "position": {
            "x": random.randint(10, 800),
            "y": random.randint(10, 500)
        },
        "size": {
            "width": random.randint(200, 400),
            "height": random.randint(150, 300)
        },
        "bg_color": random.choice(["#ffffff", "#f0f0f0", "#e0e0e0", "#d0d0d0", "#333333", "#7b3eab", "#3f51b5"]),
        "text_color": random.choice(["#000000", "#333333", "#ffffff"]),
        "content": {},
        "last_updated": datetime.now()
    }
    
    # Add content based on widget type
    if widget_type == "notes":
        notes = [
            "Remember to finish the assignment by Friday",
            "Study for the midterm next week: Chapters 3-7",
            "Group meeting at 3 PM on Thursday",
            "Office hours with Prof. Johnson: Tuesdays 2-4 PM",
            "Research paper ideas: 1. ML in healthcare 2. Blockchain security 3. NLP applications",
            "Submit project proposal by May 15th",
            "Contact Dr. Sharma about internship opportunities",
            "Complete lab report for Physics experiment",
            "Register for next semester courses",
            "Buy textbooks for new courses"
        ]
        widget["content"] = {"text": random.choice(notes)}
    
    return widget

def generate_christ_bounty_sample(creator_id, department=None):
    """Generate a sample bounty document focused on Christ University courses"""
    if not department:
        department = random.choice([
            "Computer Science", "Data Science", "Artificial Intelligence", 
            "Business Administration", "Economics", "Finance", "Marketing",  
            "Psychology", "English Literature", "History", 
            "Political Science", "Law", "Mass Communication",
            "Hotel Management", "Fashion Design"
        ])
    
    # Categories are now aligned with departments
    category = department
    
    # Create course codes specific to Christ University
    christ_course_prefixes = {
        "Computer Science": ["CSC", "CSP", "CSS", "CSD"],
        "Data Science": ["DSC", "DSP", "DSA", "DST"],
        "Artificial Intelligence": ["AIM", "AID", "AIC", "AIP", "AIR"],
        "Business Administration": ["BBA", "BAM", "BAF", "BUS"],
        "Economics": ["ECO", "ECM", "ECP", "ECT"],
        "Finance": ["FIN", "FIA", "FIM", "FIB"],
        "Marketing": ["MKT", "MKD", "MKS", "MKR"],
        "Psychology": ["PSY", "PSC", "PST", "PSR"],
        "English Literature": ["ENG", "ELT", "ELC", "ELW"],
        "History": ["HIS", "HST", "HSA", "HSW"],
        "Political Science": ["POL", "POS", "POI", "POT"],
        "Law": ["LAW", "LCP", "LCC", "LCI"],
        "Mass Communication": ["COM", "MCD", "MCJ", "MCF"],
        "Hotel Management": ["HMT", "HMS", "HMF", "HMO"],
        "Fashion Design": ["FDT", "FDD", "FDM", "FDI"]
    }
    
    # Use department-specific course prefix or default to a generic one
    prefix = random.choice(christ_course_prefixes.get(department, ["COU"]))
    course_code = f"{prefix}{random.randint(101, 499)}"
    
    # Titles based on department/category
    department_specific_titles = {
        "Computer Science": [
            f"Need help understanding {course_code}: Data Structures and Algorithms",
            f"Looking for code review on my {course_code} assignment",
            f"How to implement a balanced binary tree for {course_code}",
            f"Best approach for database design in {course_code}",
            f"Trouble with multi-threading concept in {course_code}",
            f"How to optimize my sorting algorithm for {course_code}",
            f"Help needed with Spring Boot project for {course_code}",
            f"Understanding Big O notation examples from {course_code}",
            f"Implementing REST API for {course_code} project",
            f"Debugging segmentation fault in C++ for {course_code}"
        ],
        "Data Science": [
            f"Help with statistical analysis for {course_code} project",
            f"How to clean this dataset for {course_code} assignment",
            f"Need review of my prediction model for {course_code}",
            f"Interpretation of correlation results for {course_code}",
            f"Tips for visualizing multi-dimensional data in {course_code}",
            f"Trouble with feature engineering in {course_code}",
            f"Understanding PCA implementation for {course_code}",
            f"How to improve accuracy of my classifier for {course_code}",
            f"Pandas DataFrame manipulation help for {course_code}",
            f"Explaining confusion matrix results for {course_code} project"
        ],
        "Artificial Intelligence": [
            f"Understanding backpropagation in neural networks for {course_code}",
            f"Help implementing a CNN for image recognition in {course_code}",
            f"How to fine-tune BERT for my {course_code} NLP project",
            f"Debugging my reinforcement learning agent for {course_code}",
            f"Explaining the bias-variance tradeoff in {course_code}",
            f"Implementation of A* algorithm for {course_code}",
            f"Understanding attention mechanisms in transformers for {course_code}",
            f"Help with unsupervised learning project in {course_code}",
            f"How to evaluate my ML model for {course_code} assignment",
            f"Implementing genetic algorithms for {course_code}"
        ],
        "Business Administration": [
            f"Help analyzing this case study for {course_code}",
            f"How to approach SWOT analysis for {course_code}",
            f"Understanding Porter's Five Forces model in {course_code}",
            f"Tips for effective business plan for {course_code} project",
            f"How to analyze this balance sheet for {course_code}",
            f"Understanding organizational behavior concepts in {course_code}",
            f"Help with supply chain management assignment for {course_code}",
            f"Analyzing business ethics case for {course_code}",
            f"How to approach market entry strategy for {course_code}",
            f"Understanding change management models for {course_code}"
        ],
        "Economics": [
            f"Help explaining elasticity of demand for {course_code}",
            f"Understanding macroeconomic indicators in {course_code}",
            f"How to analyze this supply-demand graph for {course_code}",
            f"Help with game theory problem in {course_code}",
            f"Understanding fiscal policy implications for {course_code}",
            f"Analyzing economic growth models for {course_code}",
            f"Help with econometrics problem set for {course_code}",
            f"Understanding Gini coefficient calculation in {course_code}",
            f"How to approach this IS-LM model problem for {course_code}",
            f"Analyzing international trade policies for {course_code}"
        ],
        "Finance": [
            f"Help calculating NPV for this investment case in {course_code}",
            f"Understanding option pricing models for {course_code}",
            f"How to approach portfolio optimization for {course_code}",
            f"Help with capital budgeting problem in {course_code}",
            f"Understanding financial statement analysis for {course_code}",
            f"How to calculate WACC for this company in {course_code}",
            f"Help with Black-Scholes model application in {course_code}",
            f"Understanding dividend policy analysis for {course_code}",
            f"How to approach risk management case in {course_code}",
            f"Analyzing merger valuation for {course_code} assignment"
        ],
        "Law": [
            f"Help understanding tort law case for {course_code}",
            f"Constitutional law interpretation for {course_code}",
            f"How to analyze this contract clause for {course_code}",
            f"Understanding legal precedent application in {course_code}",
            f"Help with criminal procedure question for {course_code}",
            f"Analyzing intellectual property case for {course_code}",
            f"Understanding international law principles for {course_code}",
            f"How to approach this legal research assignment for {course_code}",
            f"Help with legal writing assignment for {course_code}",
            f"Analyzing corporate law scenario for {course_code}"
        ],
        "Psychology": [
            f"Help designing experiment for {course_code}",
            f"Understanding cognitive bias in {course_code}",
            f"How to analyze this behavioral study for {course_code}",
            f"Help interpreting psychological assessment results for {course_code}",
            f"Understanding developmental psychology theories for {course_code}",
            f"Help with statistical analysis of survey data for {course_code}",
            f"Analyzing case study for abnormal psychology in {course_code}",
            f"Understanding neuropsychological test results for {course_code}",
            f"How to approach therapy techniques comparison for {course_code}",
            f"Analyzing social psychology experiment design for {course_code}"
        ]
    }
    
    # Generic titles for departments not specifically listed
    generic_titles = [
        f"Need help with {course_code} assignment",
        f"Struggling with {course_code} concept",
        f"How to approach this problem in {course_code}",
        f"Looking for explanation on {course_code} topic",
        f"Tips for {course_code} project",
        f"Best resources for studying {course_code}",
        f"Help understanding lecture notes from {course_code}",
        f"Need clarification on {course_code} professor's explanation",
        f"How to prepare for {course_code} exam",
        f"Study group for {course_code} - who's interested?"
    ]
    
    # Get titles for specific department or use generic ones
    available_titles = department_specific_titles.get(department, generic_titles)
    title = random.choice(available_titles)
    
    # Set complexity and reward based on the nature of the question
    complexity = random.randint(1, 5)
    reward = 25 if complexity <= 2 else 50 if complexity <= 4 else 100
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    status = random.choice(["open", "closed"])
    closed_at = get_random_date(created_at, datetime(2023, 12, 31)) if status == "closed" else None
    
    # Generate related tags
    tags_by_department = {
        "Computer Science": ["programming", "algorithms", "data structures", "web", "mobile", "AI", "ML", "database", "cloud", "security", "networking", "software engineering"],
        "Data Science": ["statistics", "machine learning", "data visualization", "big data", "analytics", "python", "R", "SQL", "pandas", "data mining", "predictive modeling"],
        "Artificial Intelligence": ["machine learning", "neural networks", "deep learning", "NLP", "computer vision", "reinforcement learning", "AI ethics", "robotics"],
        "Business Administration": ["management", "marketing", "finance", "strategy", "entrepreneurship", "operations", "human resources", "leadership", "business ethics"],
        "Economics": ["microeconomics", "macroeconomics", "econometrics", "economic policy", "game theory", "development economics", "international trade"],
        "Finance": ["investments", "corporate finance", "financial markets", "portfolio management", "risk management", "banking", "valuation", "financial modeling"],
        "Marketing": ["digital marketing", "brand management", "market research", "consumer behavior", "social media marketing", "advertising", "marketing strategy"],
        "Psychology": ["clinical", "cognitive", "developmental", "social", "experimental", "neuropsychology", "counseling", "psychological assessment"],
        "English Literature": ["literary analysis", "creative writing", "poetry", "fiction", "drama", "literary theory", "comparative literature", "cultural studies"],
        "History": ["ancient history", "medieval", "modern", "world history", "political history", "social history", "historiography", "archaeological"],
        "Political Science": ["international relations", "political theory", "comparative politics", "policy analysis", "governance", "diplomacy", "political economy"],
        "Law": ["constitutional", "criminal", "civil", "corporate", "intellectual property", "international", "human rights", "legal research", "legal writing"],
        "Mass Communication": ["journalism", "media studies", "public relations", "digital media", "broadcasting", "film", "advertising", "social media"],
        "Hotel Management": ["hospitality", "food & beverage", "hotel operations", "event management", "tourism", "customer service", "revenue management"],
        "Fashion Design": ["apparel design", "textile design", "fashion illustration", "garment construction", "trend analysis", "fashion merchandising", "sustainable fashion"]
    }
    
    # Get tags for specific department or use generic ones
    all_tags = tags_by_department.get(department, ["academics", "assignments", "exams", "projects", "study", "research", "coursework"])
    tags = random.sample(all_tags, random.randint(2, min(5, len(all_tags))))
    
    # Generate more detailed descriptions based on title
    if "code review" in title.lower():
        description = f"""I've written code for my {course_code} assignment but I'm not sure if it's optimal. The assignment is about {random.choice(['implementing a search algorithm', 'creating a web application', 'building a data processing pipeline', 'designing a database schema'])}.

Here's what I've done so far:
- Implemented the core functionality
- Added error handling
- Written some basic tests

I'm particularly concerned about:
1. Time complexity
2. Best practices
3. Edge cases I might have missed

Any feedback would be greatly appreciated, especially on how to make it more efficient and maintainable."""
    
    elif "help understanding" in title.lower():
        description = f"""I'm having trouble understanding the concept of {random.choice(['object-oriented programming', 'statistical significance', 'database normalization', 'neural networks', 'economic indicators', 'legal precedents'])} in my {course_code} course.

The professor explained it as {random.choice(['a way to organize code', 'a measure of result reliability', 'a process to optimize data storage', 'a computational model inspired by the brain', 'metrics that reflect economic health', 'past court decisions that influence current cases'])}, but I'm still confused about:

1. How it works in practice
2. When to apply it
3. Why it's important

Could someone please explain this in a simpler way with some practical examples? I've already read the textbook chapter but it didn't click for me."""
    
    elif "implement" in title.lower():
        description = f"""For my {course_code} project, I need to implement {random.choice(['a sorting algorithm', 'a REST API', 'a neural network', 'a database system', 'a financial model', 'a research methodology'])}.

The requirements are:
- Must be {random.choice(['efficient', 'scalable', 'accurate', 'reliable', 'comprehensive', 'robust'])}
- Needs to handle {random.choice(['large datasets', 'concurrent requests', 'complex inputs', 'edge cases', 'multiple scenarios', 'diverse parameters'])}
- Should follow {random.choice(['industry standards', 'best practices', 'design patterns', 'coding conventions', 'established methodologies', 'accepted frameworks'])}

I've started with {random.choice(['a basic outline', 'some pseudocode', 'initial research', 'studying examples', 'reviewing related work', 'identifying key components'])}, but I'm not sure how to proceed. Any guidance on implementation steps or approach would be very helpful."""
    
    elif "approach" in title.lower():
        description = f"""I have an assignment in {course_code} about {random.choice(['analyzing a complex system', 'solving an optimization problem', 'designing an experiment', 'developing a strategy', 'evaluating a case study', 'creating a comprehensive plan'])}.

I'm not sure what approach to take. Should I:
1. {random.choice(['Start with theoretical analysis', 'Focus on practical applications', 'Use a top-down strategy', 'Apply a bottom-up method', 'Emphasize qualitative aspects', 'Prioritize quantitative measures'])}?
2. {random.choice(['Consider multiple alternatives', 'Deep dive into one solution', 'Compare different methodologies', 'Adapt existing frameworks', 'Develop a custom approach', 'Follow standard procedures'])}?

The assignment is due in {random.randint(3, 14)} days, and I'm looking for guidance on how to structure my work and what methodology would be most appropriate for this type of problem."""
    
    else:
        # Generic description for other types of questions
        description = f"""I'm working on {title.replace("Need help with ", "").replace("Looking for ", "").replace("Help with ", "")} and I'm facing some challenges.

The main issues I'm encountering are:
1. {random.choice(['Understanding the core concepts', 'Applying the theory to practice', 'Finding relevant resources', 'Following the correct methodology', 'Interpreting the results', 'Meeting the requirements'])}
2. {random.choice(['Time constraints', 'Complexity of the material', 'Lack of examples', 'Confusing instructions', 'Technical difficulties', 'Integration challenges'])}

I've already tried {random.choice(['reading the textbook', 'watching tutorial videos', 'consulting with classmates', 'reviewing lecture notes', 'searching online resources', 'practicing with similar problems'])}, but I'm still struggling.

Any help, explanations, or resources would be greatly appreciated!"""
    
    return {
        "_id": ObjectId(),
        "creator_id": str(creator_id),
        "title": title,
        "description": description,
        "category": category,
        "complexity": complexity,
        "reward": reward,
        "status": status,
        "created_at": created_at,
        "closed_at": closed_at,
        "tags": tags
    }

def generate_detailed_bounty_response_sample(bounty_id, responder_id, is_creator_id=False, bounty_data=None):
    """Generate a detailed sample bounty response document"""
    
    # Get category if bounty_data is provided
    category = bounty_data.get('category', 'General') if bounty_data else 'General'
    
    # Define response templates based on category
    category_responses = {
        "Computer Science": [
            """Based on my understanding of the problem, this is related to algorithm complexity and data structure selection.

The key insight here is to understand the trade-offs between time and space complexity. For your specific case with {specific_problem}, I'd recommend using a {data_structure} because it offers {advantage}.

Here's a step-by-step approach:
1. First, analyze the requirements carefully - you need {requirement}
2. Consider using {algorithm} which has a time complexity of {complexity}
3. Implement it with {language} using the following pattern:
```
{code_snippet}
```

The most common mistake students make is {common_mistake}. Avoid this by {solution}.

For further reading, I'd recommend checking out {resource}. It explains the theoretical foundations really well.""",

            """I've worked on similar problems in my Advanced Algorithms course. Your issue with {specific_problem} is actually a classic case of {pattern}.

Here's what you need to do:

1. Restructure your approach to use {technique} instead of {alternative}
2. Make sure you're handling edge cases like {edge_case}
3. Optimize your solution by {optimization}

Here's a pseudocode implementation that should help:
```
{pseudocode}
```

The time complexity is {complexity} and space complexity is {space}.

I'd be happy to review your implementation if you need more specific guidance!""",

            """This is actually a common pattern in software engineering. Let me break this down:

Your {specific_problem} requires understanding {concept}, which is fundamental in CS. The solution involves:

1. Identifying the appropriate data structure: In this case, a {data_structure} is optimal because {reason}
2. Implementing an efficient algorithm: {algorithm} works well here with {complexity} time complexity
3. Optimizing for your specific constraints: Given that you mentioned {constraint}, you should focus on {focus}

Here's a code snippet that demonstrates this approach:
```
{code_snippet}
```

This pattern is widely used in industry, especially for {application}. If you're interested in learning more, check out {resource} - it's what we used in my Advanced Programming course at Christ University."""
        ],
        
        "Data Science": [
            """Your question about {specific_problem} in data analysis is interesting. Based on my experience in the Data Science program at Christ, here's my approach:

First, understand that when dealing with {data_type} data, the key challenge is usually {challenge}. To address this:

1. Start with exploratory data analysis (EDA): Check for {data_quality_issue} and {pattern}
2. For preprocessing: Apply {preprocessing} to handle {specific_issue}
3. When modeling: Consider using {model} which performs well for this type of data because {reason}

Here's a code snippet that might help:
```python
{code_snippet}
```

The most important metric to evaluate your results would be {metric} since {justification}.

A common mistake is {mistake} - I made this error in my own project for {course_code} and had to redo my analysis!""",

            """Having worked with similar datasets in my Data Mining course, I think your {specific_problem} requires careful consideration of both feature engineering and model selection.

Here's my recommendation:

1. Feature Engineering:
   - Handle missing values using {imputation_method} rather than simple deletion
   - Apply {transformation} to handle skewness in your distribution
   - Create interaction features between {feature1} and {feature2}

2. Model Selection:
   - For this type of problem, {model} tends to outperform alternatives because {reason}
   - Tune hyperparameters focusing on {parameter} which has the most impact
   - Use {validation_strategy} for validation to avoid {issue}

The expected performance should be around {performance} based on similar datasets.

Implementation note: Watch out for {warning} which can significantly affect your results."""
        ],
        
        "Business Administration": [
            """Regarding your case study on {company}, I've analyzed similar scenarios in my Strategic Management course at Christ.

The key to approaching this SWOT analysis is focusing on:

1. Strengths: Emphasize their {strength} which provides competitive advantage in {industry}
2. Weaknesses: Their {weakness} is particularly concerning given market trends toward {trend}
3. Opportunities: The recent {market_change} presents a unique opportunity to {strategy}
4. Threats: Be sure to address {threat} which has disrupted similar businesses

When formulating recommendations, concentrate on how they can leverage {leverage_point} to address {challenge}. A well-structured analysis should:

- Begin with market context (2 paragraphs)
- Detail each SWOT element with specific examples (1-2 paragraphs each)
- Provide 3-5 actionable recommendations
- Include implementation considerations

Professor {professor_name} particularly values recommendations that balance short-term feasibility with long-term strategic positioning."""
        ],
        
        "Law": [
            """Regarding your question on {legal_topic}, this case involves several important legal principles.

First, we need to consider the jurisdiction. Since this falls under {jurisdiction}, we should apply {legal_standard} as established in {precedent_case}.

The key elements to analyze are:
1. Whether {element1} is satisfied based on {fact_pattern}
2. How courts have interpreted {element2} in similar cases
3. The potential defenses available, particularly {defense}

A strong legal analysis would:
- Begin with the applicable legal standard
- Apply facts methodically to each element
- Consider counter-arguments
- Conclude with likely outcome and strength of case

Based on similar cases like {case_name} (20XX), the court would likely {outcome} because {reasoning}.

I recommend reviewing {source} which provides an excellent framework for analyzing these types of issues."""
        ],
        
        "Psychology": [
            """Your research question about {psychological_phenomenon} touches on several important theoretical frameworks.

From a {theoretical_perspective} perspective, {phenomenon} is understood as {explanation}. However, recent research by {researcher} (20XX) suggests that {alternative_view}.

For your experiment design, I recommend:
1. Using a {design_type} design to control for {confound}
2. Measuring {variable} using {instrument}, which has strong validity (α = {alpha})
3. Recruiting participants through {sampling_method} to ensure {sampling_benefit}

Statistical analysis should include {analysis_type} to test your hypothesis about {hypothesis}.

A common pitfall in this type of research is {pitfall} - I made this mistake in my own study for {course_code} and had to recollect data!

If you're interested in further reading, {source} provides an excellent contemporary framework that builds on traditional understandings."""
        ]
    }
    
    # Generic responses for categories not specifically covered
    generic_responses = [
        """Based on my understanding, the solution to your question about {topic} involves {approach}. The key is to {key_insight}.

Let me explain further:
1. First, you need to understand that {explanation_1}
2. Then, apply {method} which works because {reason}
3. Finally, make sure to {important_step}

A common misconception is {misconception}, but actually {correction}.

I had a similar assignment in my {course} course, and what helped me most was {helpful_resource}. Hope this helps with your {course_code} assignment!""",
        
        """Having worked on similar problems before, I think the best approach for your {topic} question is:

1. Start by {first_step} - this establishes the foundation
2. Then proceed to {second_step}, making sure to {important_consideration}
3. Finally, {third_step} to complete the process

The most important thing to remember is {important_point}. Many students make the mistake of {common_error}, which leads to {consequence}.

In my experience from {course}, using {technique} yields the best results because {advantage}. Let me know if you need more specific guidance!""",
        
        """I can help with your question about {topic}. This is actually a topic we covered extensively in {course}.

The approach I recommend is:

First, understand the underlying principle: {principle}

Then apply these steps:
- {step_1}
- {step_2}
- {step_3}

The key insight that many miss is {key_insight}. This makes a significant difference because {reason}.

For reference, I found {resource} extremely helpful when I was learning this concept. It explains {explanation_topic} particularly well.

Hope this helps with your assignment! Feel free to ask if anything needs further clarification."""
    ]
    
    # Select appropriate template based on category
    if category in category_responses:
        template = random.choice(category_responses[category])
    else:
        template = random.choice(generic_responses)
    
    # Fill in placeholders with relevant content
    fillers = {
        # Computer Science
        "specific_problem": ["sorting large datasets", "optimizing database queries", "implementing concurrent operations", 
                            "designing efficient algorithms", "handling edge cases", "memory management issues"],
        "data_structure": ["hash table", "balanced binary tree", "heap", "trie", "graph", "dynamic array", "linked list"],
        "advantage": ["O(1) lookup time", "balanced operations", "efficient memory usage", "natural ordering", "flexibility"],
        "requirement": ["fast lookups", "ordered traversal", "minimal memory footprint", "support for complex operations"],
        "algorithm": ["divide and conquer", "dynamic programming", "greedy approach", "backtracking", "branch and bound"],
        "complexity": ["O(n log n)", "O(n²)", "O(n)", "O(log n)", "O(1)", "O(n³)"],
        "language": ["Python", "Java", "C++", "JavaScript", "Go"],
        "code_snippet": ["def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)",
                        "class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None",
                        "public static int binarySearch(int[] array, int target) {\n    int left = 0;\n    int right = array.length - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (array[mid] == target) return mid;\n        if (array[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}",
                        "function quickSort(arr) {\n  if (arr.length <= 1) return arr;\n  const pivot = arr[Math.floor(arr.length / 2)];\n  const left = arr.filter(x => x < pivot);\n  const middle = arr.filter(x => x === pivot);\n  const right = arr.filter(x => x > pivot);\n  return [...quickSort(left), ...middle, ...quickSort(right)];\n}"],
        "common_mistake": ["not handling edge cases", "using the wrong data structure", "ignoring time complexity", 
                          "premature optimization", "not testing with diverse inputs"],
        "solution": ["testing with boundary conditions", "benchmarking different approaches", "starting with a naive solution first", 
                    "drawing out the algorithm flow", "using helper functions for clarity"],
        "resource": ["Introduction to Algorithms by CLRS", "Algorithm Design Manual by Skiena", 
                    "the Stanford Algorithm course on Coursera", "GeeksforGeeks tutorials"],
        "pattern": ["dynamic programming problem", "graph traversal challenge", "divide and conquer scenario", 
                   "tree balancing issue", "recursion with memoization opportunity"],
        "technique": ["memoization", "breadth-first search", "the greedy approach", "binary search", "backtracking"],
        "alternative": ["brute force", "recursive solution without memoization", "linear search", "nested loops"],
        "edge_case": ["empty inputs", "single element arrays", "duplicate values", "negative numbers", "extremely large inputs"],
        "optimization": ["caching intermediate results", "reducing unnecessary computation", "using more efficient data structures", 
                        "avoiding redundant checks", "implementing early termination conditions"],
        "pseudocode": ["function solve(problem):\n  if problem is simple:\n    return direct solution\n  else:\n    break problem into smaller parts\n    solve each part recursively\n    combine solutions\n    return combined solution",
                      "for each element in collection:\n  if element meets condition:\n    process element\n    update result\n  else:\n    skip to next element\nreturn final result"],
        "space": ["O(n)", "O(n²)", "O(log n)", "O(1)", "O(n log n)"],
        "concept": ["asymptotic analysis", "recursion", "object-oriented principles", "memory management", 
                   "concurrent programming", "design patterns"],
        "reason": ["it provides constant-time lookups", "it maintains element ordering", "it optimizes for your access pattern", 
                  "it has lower memory overhead", "it handles collisions efficiently"],
        "constraint": ["memory limitations", "performance requirements", "API compatibility", "platform restrictions"],
        "focus": ["time efficiency", "space efficiency", "code readability", "maintainability", "error handling"],
        "application": ["web services", "data processing pipelines", "real-time systems", "mobile applications", "database implementations"],
        
        # Data Science
        "data_type": ["time series", "categorical", "high-dimensional", "imbalanced", "sparse", "textual", "image"],
        "challenge": ["identifying patterns without overfitting", "handling missing values", "feature selection", 
                     "dealing with class imbalance", "preprocessing effectively"],
        "data_quality_issue": ["missing values", "outliers", "class imbalance", "multicollinearity", "skewed distributions"],
        "pattern": ["seasonality", "clusters", "correlations", "outliers", "trends"],
        "preprocessing": ["normalization", "one-hot encoding", "feature scaling", "dimensionality reduction", "tokenization"],
        "specific_issue": ["missing values", "outliers", "skewed distributions", "high cardinality features"],
        "model": ["Random Forest", "Gradient Boosting", "Neural Network", "Support Vector Machine", "Logistic Regression", "LSTM"],
        "metric": ["F1-score", "AUC-ROC", "precision", "recall", "mean squared error", "silhouette score"],
        "justification": ["it balances precision and recall", "it works well with imbalanced data", 
                         "it's robust to outliers", "it captures prediction error effectively"],
        "mistake": ["not scaling features", "using accuracy for imbalanced data", "overfitting to the training set", 
                   "not handling missing values properly", "ignoring data leakage"],
        "course_code": ["DSC301", "DSC405", "DSA220", "AID389", "DST456"],
        "imputation_method": ["KNN imputation", "mean/median imputation", "regression imputation", "multiple imputation"],
        "transformation": ["log transformation", "Box-Cox", "quantile transformation", "standardization"],
        "feature1": ["categorical variables", "timestamp", "numerical features", "text data"],
        "feature2": ["continuous variables", "geographical data", "customer attributes", "product features"],
        "validation_strategy": ["k-fold cross-validation", "stratified sampling", "time-series split", "leave-one-out"],
        "issue": ["data leakage", "overfitting", "selection bias", "temporal dependencies"],
        "performance": ["85-90% accuracy", "0.7-0.8 F1 score", "AUC around 0.85", "20-25% error reduction"],
        "warning": ["class imbalance", "feature correlation", "data leakage through preprocessing", "overfitting to validation set"],
        
        # Business
        "company": ["Amazon", "Tesla", "Apple", "Microsoft", "Google", "Reliance Industries", "Tata Consultancy Services", "HDFC Bank"],
        "strength": ["robust supply chain", "innovative product line", "strong brand recognition", "skilled workforce", 
                    "proprietary technology", "extensive distribution network"],
        "industry": ["e-commerce", "automotive", "technology", "financial services", "telecommunications", "healthcare"],
        "weakness": ["high operating costs", "dependence on single market", "aging infrastructure", "limited product diversity", 
                    "employee turnover", "customer service issues"],
        "trend": ["sustainability", "digital transformation", "remote work", "personalization", "automation"],
        "market_change": ["regulatory shift", "technological breakthrough", "consumer behavior change", 
                         "emerging market opening", "competitor consolidation"],
        "strategy": ["enter new markets", "develop complementary products", "form strategic partnerships", 
                    "implement vertical integration", "adapt pricing strategy"],
        "threat": ["new market entrant", "disruptive technology", "changing regulations", "economic downturn", 
                  "supply chain disruption", "cybersecurity vulnerability"],
        "leverage_point": ["customer data", "R&D capabilities", "distribution network", "brand equity", 
                          "organizational culture", "financial reserves"],
        "challenge": ["market saturation", "technology adoption", "talent acquisition", "cost pressure", 
                     "competitive intensity", "regulatory compliance"],
        "professor_name": ["Dr. Sharma", "Dr. Patel", "Prof. Mehta", "Dr. Reddy", "Prof. Singh", "Dr. Thomas"],
        
        # Law
        "legal_topic": ["contract interpretation", "tort liability", "constitutional rights", "property dispute", 
                       "criminal procedure", "intellectual property infringement"],
        "jurisdiction": ["contract law", "tort law", "criminal law", "constitutional law", "corporate law", "international law"],
        "legal_standard": ["reasonable person standard", "strict liability", "beyond reasonable doubt", 
                          "preponderance of evidence", "business judgment rule"],
        "precedent_case": ["Smith v. Jones (2010)", "State v. Johnson (2015)", "Patel Industries v. Global Corp (2018)", 
                          "Constitutional Bench decision in Kumar v. State (2012)"],
        "element1": ["duty of care", "consideration", "mens rea", "actual malice", "fair use", "undue influence"],
        "fact_pattern": ["the written agreement terms", "defendant's actions", "surrounding circumstances", 
                        "industry standards", "prior conduct"],
        "element2": ["causation", "acceptance", "reasonable expectation of privacy", "actual damages", "substantial similarity"],
        "defense": ["necessity", "duress", "statute of limitations", "fair use", "lack of capacity", "self-defense"],
        "case_name": ["Mehta v. Singh", "State of Karnataka v. Reddy", "National Bank v. Secure Systems Ltd.", 
                     "Constitutional challenge to Section 377"],
        "outcome": ["rule in favor of the plaintiff", "dismiss the case", "remand for further proceedings", 
                   "uphold the lower court's decision", "issue an injunction"],
        "reasoning": ["the elements of the claim were clearly established", "precedent strongly supports this interpretation", 
                     "public policy considerations", "statutory language is unambiguous"],
        "source": ["SCC Online Database", "All India Reporter", "Legal Commentary by Justice Chandrachud", 
                  "Indian Contract Act Commentary", "Christ University Law Review"],
        
        # Psychology
        "psychological_phenomenon": ["cognitive dissonance", "confirmation bias", "attachment styles", "group polarization", 
                                    "learned helplessness", "prosocial behavior"],
        "theoretical_perspective": ["cognitive", "behavioral", "psychoanalytic", "humanistic", "evolutionary", "sociocultural"],
        "phenomenon": ["memory formation", "attitude change", "identity development", "cognitive bias", "emotional regulation"],
        "explanation": ["a result of conflicting beliefs", "an adaptive evolutionary mechanism", 
                       "influenced by early childhood experiences", "a product of social learning"],
        "researcher": ["Dr. Sharma", "Prof. Bhat", "Dr. Menon", "Prof. Rao", "Dr. Patel"],
        "alternative_view": ["individual differences play a greater role", "cultural factors significantly modify the effect", 
                            "neurological mechanisms better explain the variation", "contextual factors determine outcomes"],
        "design_type": ["between-subjects", "within-subjects", "mixed methods", "longitudinal", "cross-sectional"],
        "confound": ["demand characteristics", "order effects", "selection bias", "maturation", "testing effects"],
        "variable": ["self-reported anxiety", "reaction time", "accuracy", "physiological arousal", "behavioral indicators"],
        "instrument": ["Beck Depression Inventory", "implicit association test", "structured clinical interview", 
                      "behavioral observation protocol", "standardized assessment"],
        "alpha": ["0.87", "0.92", "0.76", "0.83", "0.95"],
        "sampling_method": ["stratified random sampling", "convenience sampling", "snowball sampling", 
                           "quota sampling", "purposive sampling"],
        "sampling_benefit": ["representativeness", "adequate statistical power", "ecological validity", 
                            "demographic diversity", "theoretical saturation"],
        "analysis_type": ["ANOVA", "multiple regression", "structural equation modeling", "thematic analysis", "factor analysis"],
        "hypothesis": ["the relationship between variables", "group differences", "predictive factors", 
                      "moderating influences", "mediation effects"],
        "pitfall": ["failing to control for confounding variables", "using unreliable measures", 
                   "insufficient sample size", "participant bias", "researcher expectancy effects"],
        
        # Generic
        "topic": ["the assignment", "this concept", "your research question", "the case study", "this problem", "your project"],
        "approach": ["breaking down the problem into smaller steps", "applying theoretical models to practical scenarios", 
                    "using a systematic analysis framework", "combining multiple perspectives", "starting with first principles"],
        "key_insight": ["focus on the underlying patterns", "understand the relationship between concepts", 
                       "identify the critical constraints", "recognize the fundamental assumptions"],
        "explanation_1": ["the theory builds upon foundational principles", "practical applications differ from theoretical models", 
                         "context significantly influences outcomes", "multiple factors interact in complex ways"],
        "method": ["comparative analysis", "systematic evaluation", "structured approach", "iterative process"],
        "reason": ["it addresses the core issues directly", "it has proven effective in similar situations", 
                  "it balances competing considerations", "it accounts for important variables"],
        "important_step": ["validate your results", "consider alternative interpretations", "document your assumptions", 
                          "connect back to the original question", "address potential criticisms"],
        "misconception": ["focusing only on obvious factors", "oversimplifying complex relationships", 
                         "neglecting important context", "assuming linear causality"],
        "correction": ["multiple factors are usually involved", "the relationship is more nuanced", 
                      "contextual factors critically matter", "feedback loops often exist"],
        "course": ["Research Methods", "Advanced Theory", "Practical Applications", "Case Studies", "Core Principles"],
        "helpful_resource": ["the textbook chapter on related concepts", "consulting with teaching assistants", 
                            "reviewing lecture notes carefully", "practicing with similar examples"],
        "course_code": ["CSC301", "BUS405", "PSY220", "LAW389", "ECO456", "ENG331", "MKT270"],
        "first_step": ["clearly defining the problem scope", "reviewing relevant theories", 
                      "gathering necessary information", "identifying key variables"],
        "second_step": ["analyzing relationships between factors", "applying appropriate methods", 
                       "evaluating alternative approaches", "organizing your analysis systematically"],
        "important_consideration": ["account for limitations", "maintain logical consistency", 
                                  "support claims with evidence", "acknowledge competing perspectives"],
        "third_step": ["synthesize your findings", "draw well-supported conclusions", 
                      "connect back to theoretical frameworks", "suggest practical implications"],
        "important_point": ["consistency in your methodology", "clarity in your reasoning", 
                          "thoroughness in your analysis", "precision in your terminology"],
        "common_error": ["rushing through preliminary analysis", "overlooking important details", 
                        "using inappropriate methods", "making unsupported assertions"],
        "consequence": ["incomplete solutions", "inaccurate conclusions", "logical inconsistencies", "missed opportunities"],
        "technique": ["structured analysis framework", "comparative evaluation", "systematic problem-solving approach", 
                     "iterative refinement process", "interdisciplinary perspective"],
        "advantage": ["it addresses complexity more effectively", "it leads to more reliable results", 
                     "it integrates multiple perspectives", "it aligns with current best practices"],
        "principle": ["concepts build upon foundational elements", "theory and practice are complementary", 
                     "context shapes application", "relationships between factors matter more than individual components"],
        "step_1": ["Define your scope and objectives clearly", "Identify the relevant theoretical frameworks", 
                  "Gather all necessary information", "Map out key variables and relationships"],
        "step_2": ["Apply analytical methods systematically", "Consider multiple perspectives", 
                  "Evaluate alternatives thoroughly", "Document your reasoning process"],
        "step_3": ["Synthesize findings cohesively", "Connect conclusions back to original questions", 
                  "Acknowledge limitations appropriately", "Suggest practical implications"],
        "key_insight": ["the relationship between theory and application", "how different factors interact", 
                       "which variables have the most influence", "when and why exceptions occur"],
        "resource": ["the supplementary readings from week 5", "the case studies in chapter 7", 
                    "Professor Kumar's lecture notes", "the workshop materials from last semester"]
    }
    
    # Replace placeholders with relevant content
    for placeholder in fillers:
        if "{" + placeholder + "}" in template:
            replacement = random.choice(fillers[placeholder])
            template = template.replace("{" + placeholder + "}", replacement)
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "bounty_id": bounty_id,
        "responder_id": str(responder_id),
        "content": template,
        "upvotes": random.randint(0, 15),
        "downvotes": random.randint(0, 5),
        "is_pinned": True if is_creator_id else random.random() < 0.3,  # Higher chance of being pinned if it's the creator
        "created_at": created_at
    }

def generate_bounty_vote_sample(bounty_response_id, user_id):
    """Generate a sample bounty vote document"""
    vote_type = random.choice(["up", "down"])
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "bounty_response_id": bounty_response_id,
        "user_id": str(user_id),
        "vote_type": vote_type,
        "created_at": created_at
    }

def generate_marketplace_listing_sample(seller_id, department=None):
    """Generate a sample marketplace listing document"""
    if not department:
        department = random.choice([
            "Computer Science", "Data Science", "Artificial Intelligence", 
            "Business Administration", "Economics", "Finance", "Marketing",  
            "Psychology", "English Literature", "History", 
            "Political Science", "Law", "Mass Communication",
            "Hotel Management", "Fashion Design"
        ])
    
    types = ["notes", "service", "template", "study guide", "practice tests", "research paper"]
    listing_type = random.choice(types)
    
    # Create Christ University specific course codes
    christ_course_prefixes = {
        "Computer Science": ["CSC", "CSP", "CSS", "CSD"],
        "Data Science": ["DSC", "DSP", "DSA", "DST"],
        "Artificial Intelligence": ["AIM", "AID", "AIC", "AIP", "AIR"],
        "Business Administration": ["BBA", "BAM", "BAF", "BUS"],
        "Economics": ["ECO", "ECM", "ECP", "ECT"],
        "Finance": ["FIN", "FIA", "FIM", "FIB"],
        "Marketing": ["MKT", "MKD", "MKS", "MKR"],
        "Psychology": ["PSY", "PSC", "PST", "PSR"],
        "English Literature": ["ENG", "ELT", "ELC", "ELW"],
        "History": ["HIS", "HST", "HSA", "HSW"],
        "Political Science": ["POL", "POS", "POI", "POT"],
        "Law": ["LAW", "LCP", "LCC", "LCI"],
        "Mass Communication": ["COM", "MCD", "MCJ", "MCF"],
        "Hotel Management": ["HMT", "HMS", "HMF", "HMO"],
        "Fashion Design": ["FDT", "FDD", "FDM", "FDI"]
    }
    
    # Use department-specific course prefix or default to a generic one
    prefix = random.choice(christ_course_prefixes.get(department, ["COU"]))
    course_code = f"{prefix}{random.randint(101, 499)}"
    
    # Titles based on department and listing type
    department_specific_titles = {
        "Computer Science": [
            f"{course_code} Complete Programming Notes",
            f"{course_code} Algorithms & Data Structures Guide",
            f"Web Development Project Template for {course_code}",
            f"Python Programming Practice Tests - {course_code}",
            f"Database Design Study Guide for {course_code}"
        ],
        "Data Science": [
            f"{course_code} Statistical Analysis Notes",
            f"{course_code} Machine Learning Guide",
            f"Data Visualization Templates for {course_code}",
            f"Big Data Analytics Study Guide - {course_code}",
            f"Python for Data Science Practice Tests - {course_code}"
        ],
        "Business Administration": [
            f"{course_code} Marketing Strategy Framework",
            f"{course_code} Business Plan Template",
            f"Financial Analysis Study Guide for {course_code}",
            f"Management Case Studies - {course_code}",
            f"Business Research Methods Notes - {course_code}"
        ],
        "Law": [
            f"{course_code} Constitutional Law Notes",
            f"{course_code} Legal Case Analysis Template",
            f"Contract Law Study Guide - {course_code}",
            f"Legal Research Method Notes - {course_code}",
            f"Criminal Procedure Practice Questions - {course_code}"
        ]
    }
    
    # Generic titles for other departments
    generic_titles = [
        f"{course_code} Comprehensive Notes",
        f"{course_code} Study Guide",
        f"Project Template for {course_code}",
        f"Practice Tests for {course_code}",
        f"Research Paper Template - {course_code}",
        f"Exam Preparation Guide for {course_code}"
    ]
    
    # Get titles for specific department or use generic ones
    available_titles = department_specific_titles.get(department, generic_titles)
    title_template = random.choice(available_titles)
    
    # Create detailed title based on listing type
    if listing_type == "notes":
        title = f"{title_template} - Complete Semester Coverage"
    elif listing_type == "service":
        title = f"Tutoring Service for {course_code} - {department}"
    elif listing_type == "template":
        title = f"Professional {title_template}"
    elif listing_type == "study guide":
        title = f"Comprehensive {title_template}"
    elif listing_type == "practice tests":
        title = f"50+ Practice Questions for {course_code}"
    elif listing_type == "research paper":
        title = f"Research Paper on {title_template.replace('Template', 'Topic')}"
    else:
        title = title_template
    
    # Create detailed descriptions based on listing type
    descriptions = {
        "notes": [
            f"Detailed class notes covering all topics from the {course_code} semester. Includes diagrams, examples, and explanations of key concepts. Perfect for exam preparation.",
            f"Comprehensive notes from {course_code} lectures and textbook readings. Well-organized and easy to follow with highlighted important points and summary sections for quick review.",
            f"Complete set of notes for {course_code} with detailed explanations and practical examples. Created by a student who received an A grade in this course."
        ],
        "service": [
            f"One-on-one tutoring sessions for {course_code} to help you understand complex concepts and solve difficult problems. Personalized assistance from a top student in {department}.",
            f"Professional help with {course_code} assignments, including step-by-step explanations and concept clarification. Guaranteed improvement in your understanding and grades.",
            f"Personalized {course_code} tutoring tailored to your learning style and specific areas of difficulty. Sessions can be scheduled at your convenience."
        ],
        "template": [
            f"Professional template for {course_code} that follows all academic formatting requirements. Just fill in your content and submit with confidence!",
            f"Ready-to-use template for {course_code} with proper structure, citations format, and styling for optimal presentation. Save time and ensure consistent quality.",
            f"Time-saving template for {course_code} with pre-formatted sections and examples to guide your work. Includes guidelines specific to Christ University requirements."
        ],
        "study guide": [
            f"Comprehensive study guide covering all exam topics for {course_code} with practice questions and solutions. Created based on previous years' exams.",
            f"Condensed review of all key concepts, formulas, and techniques you need to know for {course_code} exams. Includes quick reference sheets for last-minute review.",
            f"Strategic study guide focusing on the most important topics and likely exam questions for {course_code}. Includes study plan and memory techniques."
        ],
        "practice tests": [
            f"Collection of 50+ practice problems with detailed solutions to help you prepare for {course_code} exams. Covers all major topics from the course.",
            f"Mock exams that mimic the actual {course_code} test format and difficulty level, with answer explanations. Perfect for assessing your exam readiness.",
            f"Extensive set of practice questions for {course_code} covering all topics, organized by difficulty level. Created based on past exam patterns at Christ University."
        ],
        "research paper": [
            f"Well-researched paper on {course_code} topics with comprehensive analysis and up-to-date references. Can be used as a reference for your own research.",
            f"In-depth exploration of current research and findings in {course_code}, perfect for understanding the state of the field and identifying research gaps.",
            f"Structured analysis of key research papers related to {course_code} with synthesis of main findings and future directions. Follows Christ University research formatting guidelines."
        ]
    }
    
    description = random.choice(descriptions[listing_type])
    price = random.choice([50, 75, 100, 150, 200, 250, 300]) if listing_type == "service" else random.choice([20, 30, 40, 50, 75, 100])
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "seller_id": str(seller_id),
        "title": title,
        "description": description,
        "type": listing_type,
        "price": price,
        "file_path": f"/static/marketplace/{listing_type}_{random.randint(1000, 9999)}.pdf" if listing_type != "service" else None,
        "preview_path": f"/static/marketplace/previews/preview_{random.randint(1000, 9999)}.jpg",
        "created_at": created_at,
        "category": department,
        "subject": course_code,
        "downloads": random.randint(0, 50) if listing_type != "service" else 0
    }

def generate_marketplace_transaction_sample(listing_id, listing_data, buyer_id):
    """Generate a sample marketplace transaction document"""
    transaction_date = get_random_date(listing_data["created_at"], datetime(2023, 12, 31))
    
    review_rating = random.choices([3, 4, 5], weights=[1, 3, 6])[0]  # Weighted towards higher ratings
    
    review_texts = {
        3: [
            "Decent material but could be more comprehensive.",
            "Helpful but has some gaps in content.",
            "Good value for the price, but needs more examples.",
            "Useful information though organization could be improved.",
            "Satisfactory content but expected more detail."
        ],
        4: [
            "Very helpful material with good explanations.",
            "Well-structured content that was easy to follow.",
            "Great value for money. Definitely helped me understand the subject better.",
            "Excellent quality with minor areas for improvement.",
            "Comprehensive coverage of the topic. Would recommend."
        ],
        5: [
            "Absolutely perfect! Exactly what I needed.",
            "Outstanding quality and extremely helpful for my coursework.",
            "Saved me hours of study time. Comprehensive and clear.",
            "Best study material I've found. Worth every coin!",
            "Excellent detail and organization. Will definitely buy from this seller again."
        ]
    }
    
    review_text = random.choice(review_texts[review_rating])
    
    return {
        "_id": ObjectId(),
        "listing_id": listing_id,
        "buyer_id": str(buyer_id),
        "seller_id": str(listing_data["seller_id"]),
        "price": listing_data["price"],
        "transaction_date": transaction_date,
        "review_rating": review_rating,
        "review_text": review_text
    }

def generate_subreddit_sample():
    """Generate a sample subreddit document with a unique name"""
    global generated_subreddit_names
    
    max_attempts = 10  # Limit the number of attempts to avoid infinite loops
    
    for attempt in range(max_attempts):
        # Create subreddit templates focused on Christ University
        subreddit_templates = [
            "Christ {department} Students",
            "Christ University {campus}",
            "Christ {course_code} Group",
            "{department} at Christ",
            "{activity} at Christ University",
            "Christ {year} Batch"
        ]
        
        departments = ["Computer Science", "Data Science", "Business", "Law", "Engineering", "Arts", 
                      "Medicine", "Psychology", "Literature", "Economics", "Mathematics"]
        
        campuses = ["Main Campus", "Kengeri Campus", "BGR Campus", "Lavasa Campus", "Delhi NCR Campus", 
                   "Yeshwanthpur Campus", "School of Business", "School of Law"]
        
        course_codes = ["CSC301", "BUS405", "LAW220", "ENG389", "MED456", "PSY331", "DSC270", 
                       "ECO180", "MAT215", "COM301", "PHY210", "CHE250"]
        
        activities = ["Sports", "Cultural Club", "Debate", "Music", "Dance", "Photography", 
                     "Coding Club", "Art", "Theatre", "Entrepreneurship", "Research"]
        
        years = ["2022", "2023", "2024", "2025", "Freshers", "Final Year", "Alumni"]
        
        template = random.choice(subreddit_templates)
        if "{department}" in template:
            template = template.replace("{department}", random.choice(departments))
        if "{campus}" in template:
            template = template.replace("{campus}", random.choice(campuses))
        if "{course_code}" in template:
            template = template.replace("{course_code}", random.choice(course_codes))
        if "{activity}" in template:
            template = template.replace("{activity}", random.choice(activities))
        if "{year}" in template:
            template = template.replace("{year}", random.choice(years))
        
        name = template
        
        # Check if this name is already used
        if name not in generated_subreddit_names:
            generated_subreddit_names.add(name)
            
            # Rest of the function remains the same
            description_templates = [
                "A community for Christ University {name} students to discuss coursework, share resources, and connect.",
                "The unofficial subreddit for {name}. Ask questions, share information, and help fellow students.",
                "A place for {name} to discuss academics, campus life, and share helpful resources.",
                "Connect with other {name} at Christ University for study groups, notes sharing, and discussions.",
                "A forum for {name} to network, share knowledge, and support each other academically and professionally."
            ]
            
            description = random.choice(description_templates).replace("{name}", name)
            
            tags = []
            for word in name.split():
                if word not in ["and", "or", "the", "for", "of", "in", "on", "a", "an", "at"]:
                    tags.append(word.lower())
            
            return {
                "_id": ObjectId(),
                "name": name,
                "description": description,
                "creator_id": None,  # Will be set later
                "tags": tags[:5],  # Limit to 5 tags
                "created_at": get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31)),
                "member_count": random.randint(5, 500)
            }
    
    # If we reach here, we couldn't generate a unique name after max_attempts
    # Add a timestamp to make the name unique
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name = f"Christ University General Discussion {timestamp}"
    generated_subreddit_names.add(name)
    
    return {
        "_id": ObjectId(),
        "name": name,
        "description": f"A general discussion forum for Christ University students on all topics.",
        "creator_id": None,
        "tags": ["christ", "university", "general", "discussion"],
        "created_at": get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31)),
        "member_count": random.randint(5, 500)
    }

def generate_thread_sample(subreddit_id, creator_id, subreddit_name=None):
    """Generate a sample thread document relevant to Christ University"""
    thread_types = ["question", "debate", "project", "resource", "discussion"]
    thread_type = random.choice(thread_types)
    
    # Christ University specific course codes
    course_codes = ["CSC301", "BUS405", "LAW220", "ENG389", "MED456", "PSY331", "DSC270", 
                   "ECO180", "MAT215", "COM301", "PHY210", "CHE250", "AID180", "FIN270", "MKT350"]
    
    # Christ University professor names
    professor_names = ["Dr. Sharma", "Dr. Patel", "Prof. Mehta", "Dr. Reddy", "Prof. Singh", "Dr. Thomas",
                       "Dr. Kumar", "Prof. Joshi", "Dr. Bhat", "Prof. Rao", "Dr. Nair", "Prof. Menon"]
    
    # Christ University events and activities
    events = ["Blossoms Cultural Fest", "In-Bloom Technical Fest", "Christ MUN", "Annual Sports Meet",
             "Management Conclave", "Christ Literary Fest", "Psych Symposium", "Legal Aid Workshop",
             "Entrepreneurship Summit", "Research Day", "Alumni Connect", "Freshers' Welcome"]
    
    # Christ University campus locations
    locations = ["Main Auditorium", "Knowledge Centre", "Central Block", "Science Block", "Hostel Mess",
                "Christ Football Ground", "Central Library", "MBA Block", "Law School Building",
                "CSA Hall", "Playground", "Christ School of Business", "Cafeteria"]
    
    # Titles based on thread type
    if thread_type == "question":
        titles = [
            f"How to prepare for {random.choice(course_codes)} end semester exam?",
            f"Anyone have notes for {random.choice(professor_names)}'s class?",
            f"What are the attendance requirements for {random.choice(course_codes)}?",
            f"Tips for {random.choice(course_codes)} project submission?",
            f"How is the placement scenario for {random.choice(['CS', 'Data Science', 'MBA', 'Law', 'Engineering'])} students?",
            f"Is anyone else having issues with the new campus portal?",
            f"What are good internship opportunities for Christ {random.choice(['CS', 'Business', 'Law', 'Arts', 'Science'])} students?",
            f"How strict is the dress code policy at {random.choice(['Main Campus', 'BGR Campus', 'Kengeri Campus'])}?",
            f"Best electives to choose for {random.choice(['5th sem CS', '3rd sem MBA', '4th sem Law', '2nd sem Data Science'])}?",
            f"Any advice for new students coming to Christ University?"
        ]
    elif thread_type == "debate":
        titles = [
            f"Is {random.choice(course_codes)} course content up-to-date with industry requirements?",
            f"Should attendance requirement be reduced from 85% to 75%?",
            f"Are continuous assessments better than semester-end exams?",
            f"Main Campus vs. {random.choice(['Kengeri Campus', 'BGR Campus'])}: Which has better facilities?",
            f"Is the new grading system better than the old one?",
            f"Should Christ University have more industry collaboration?",
            f"Is the dress code policy too strict at Christ University?",
            f"Should research be mandatory for all undergraduate programs?",
            f"Are technical fests more beneficial than cultural fests?",
            f"Should Christ University allow more student-run organizations?"
        ]
    elif thread_type == "project":
        titles = [
            f"Looking for team members for {random.choice(course_codes)} project",
            f"Showcase: Our innovative project for {random.choice(events)}",
            f"Need advice on my research project under {random.choice(professor_names)}",
            f"Project idea: {random.choice(['AR app for campus navigation', 'Student networking platform', 'Study group finder', 'Campus event notification system', 'Attendance tracking app'])}",
            f"Any suggestions for {random.choice(course_codes)} final year project topics?",
            f"Technical challenges in my {random.choice(['Machine Learning', 'Web Development', 'Mobile App', 'IoT', 'Blockchain'])} project",
            f"Seeking feedback on my {random.choice(['Business plan', 'Case study analysis', 'Research proposal', 'UI/UX design', 'Marketing strategy'])}",
            f"How to approach data collection for my {random.choice(course_codes)} research project?",
            f"Project management tools recommended for student projects?",
            f"Collaborators needed for interdisciplinary project on {random.choice(['AI in healthcare', 'Sustainable business models', 'Digital marketing analytics', 'Legal tech solutions', 'Educational technology'])}"
        ]
    elif thread_type == "resource":
        titles = [
            f"Complete notes collection for {random.choice(course_codes)}",
            f"Recommended books for {random.choice(course_codes)}",
            f"Useful websites for {random.choice(['CS', 'Business', 'Law', 'Data Science', 'Engineering'])} students",
            f"Previous year question papers for {random.choice(course_codes)}",
            f"Video lecture resources to supplement {random.choice(course_codes)}",
            f"Internship opportunities for Christ University students",
            f"Study material compilation for competitive exams",
            f"Free software tools available for Christ students",
            f"Research journals accessible through Christ library",
            f"Templates for assignments and projects as per Christ format"
        ]
    else:  # discussion
        titles = [
            f"Thoughts on this semester's {random.choice(course_codes)} course structure?",
            f"Let's discuss the upcoming {random.choice(events)}",
            f"How is everyone finding the new facilities at {random.choice(locations)}?",
            f"Experiences with {random.choice(professor_names)}'s teaching style?",
            f"What are your career plans after graduating from Christ?",
            f"How does Christ University compare to other universities in India?",
            f"Balancing academics and extracurriculars at Christ",
            f"Your experience with campus placements at Christ",
            f"Food options around {random.choice(['Main Campus', 'BGR Campus', 'Kengeri Campus'])}",
            f"How is the hostel life at Christ University?"
        ]
    
    title = random.choice(titles)
    
    # Generate content based on title and type
    # Extract keywords from title to make content more relevant
    title_words = title.lower().split()
    
    # Create more detailed and relevant thread content
    if "exam" in title.lower() or "prepare" in title.lower():
        content = f"""I'm trying to prepare for the {random.choice(course_codes)} end semester exam, and I'm a bit overwhelmed with the syllabus. 

The main topics that I'm finding challenging are:
1. {random.choice(['Advanced concepts in Section 4', 'The practical applications in Unit 3', 'Theoretical frameworks from Unit 5', 'Mathematical derivations in Module 2'])}
2. {random.choice(['Case studies from the last three chapters', 'Programming exercises from the lab manual', 'Analysis techniques covered in Week 7', 'Research methodology section'])}

I've been reviewing the lecture notes and textbook, but I'm wondering if there are any other effective study strategies or resources that have worked for you all. Has anyone from previous batches shared any tips on what topics {random.choice(professor_names)} focuses on in the exams?

Also, is it true that the exam will have {random.choice(['more practical questions this year', 'a new section on applications', 'questions from additional readings', 'case-based problems'])}? Any advice would be greatly appreciated!"""
    
    elif "notes" in title.lower():
        content = f"""I missed a few classes of {random.choice(professor_names)}'s lectures due to {random.choice(['health issues', 'family emergency', 'participation in an inter-college event', 'internship interview'])}, and I'm trying to catch up before the CIA exams next week.

Specifically, I'm looking for notes on:
- {random.choice(['Chapter 7: Advanced Applications', 'Unit 4: Theoretical Frameworks', 'Module 3: Case Study Analysis', 'Week 5-6 lectures on core concepts'])}
- {random.choice(['The practical examples covered in class', 'Derivations that were explained on the board', 'Case studies that might come in the exam', 'Important formulas and their applications'])}

If anyone is willing to share their notes or has any recorded lectures, it would be incredibly helpful. I'm happy to exchange with my notes from {random.choice(['other subjects', 'previous modules', 'the first half of the semester', 'the supplementary readings'])}.

Thanks in advance for your help! I promise to pay it forward when someone else needs notes in the future."""
    
    elif "project" in title.lower():
        content = f"""I'm working on my project for {random.choice(course_codes)} under the guidance of {random.choice(professor_names)}, and I'm looking for team members who are interested in {random.choice(['machine learning applications', 'web development', 'market research', 'financial analysis', 'legal case studies', 'UX design'])}.

The project involves:
- {random.choice(['Developing a prototype application', 'Conducting primary research', 'Analyzing industry data', 'Creating an innovative solution', 'Implementing a theoretical framework'])}
- {random.choice(['Using technologies like Python, TensorFlow, and AWS', 'Applying concepts from marketing and consumer behavior', 'Integrating financial modeling techniques', 'Conducting user research and testing', 'Analyzing legal precedents and their applications'])}
- {random.choice(['Targeting completion by the end of this semester', 'Presentation in the upcoming technical symposium', 'Submission for the departmental competition', 'Potential publication in a student journal', 'Demo during the annual project exhibition'])}

Ideal team members would have skills in {random.choice(['programming and data analysis', 'research methodology and report writing', 'design thinking and prototyping', 'presentation and documentation', 'market analysis and strategy formulation'])}.

The project has significant potential for {random.choice(['practical industry applications', 'academic recognition', 'solving real-world problems', 'publication in student journals', 'showcasing in your portfolio'])}.

Please comment or DM me if you're interested in joining or want more details!"""
    
    elif "debate" in title.lower() or "vs" in title.lower() or "should" in title.lower():
        content = f"""I wanted to start a discussion about {title.lower().replace('?', '')}, as it's something that affects many of us at Christ University.

On one hand, {random.choice(['the current system provides structure and discipline', 'traditional approaches have proven effective over time', 'existing policies ensure quality and standards', 'the administration has valid reasons for the current setup', 'maintaining the status quo has certain advantages'])}.

However, I believe that {random.choice(['changes could better prepare us for industry requirements', 'more flexibility would benefit student learning', 'updates are needed to keep pace with other top universities', 'modifications could improve the overall student experience', 'reforms could address current pain points without compromising quality'])}.

Some specific points to consider:
1. {random.choice(['Impact on student stress levels and mental health', 'Effect on actual learning outcomes versus mere compliance', 'Alignment with industry expectations and requirements', 'Comparison with practices at other leading institutions', 'Long-term benefits versus short-term adjustments'])}
2. {random.choice(['Balance between academic rigor and practical application', 'Student autonomy versus institutional guidance', 'Tradition versus innovation in educational approaches', 'Standardization versus personalization in learning', 'Administrative feasibility versus ideal scenarios'])}

I'm curious to hear perspectives from other students, especially those who have {random.choice(['experienced both systems', 'studied at other institutions', 'interned in industry settings', 'different academic backgrounds', 'perspectives from various departments'])}.

What do you think? Would changes be beneficial, or should we maintain the current approach?"""
    
    elif "resource" in title.lower() or "recommended" in title.lower() or "material" in title.lower():
        content = f"""After struggling to find good resources for {random.choice(course_codes)}, I've compiled a list that might help other Christ University students.

**Textbooks:**
- {random.choice(['Smith, J. (2022). Advanced Concepts in Modern Applications', 'Patel, R. (2021). Theoretical Foundations and Practice', 'Kumar, A. (2023). Comprehensive Guide to Core Principles', 'Reddy, M. (2022). Applied Methods and Techniques'])}
- {random.choice(['Johnson, H. (2021). Practical Approaches to Complex Problems', 'Sharma, V. (2023). Fundamentals and Applications', 'Gupta, S. (2022). Modern Perspectives and Case Studies', 'Nair, P. (2021). Analysis and Implementation'])}

**Online Resources:**
- {random.choice(['MIT OpenCourseWare: Excellent lecture videos on related topics', 'Coursera: "Specialization in Advanced Applications" - first month free with student email', 'YouTube Channel: "Academic Explanations" - clear tutorials on complex topics', 'edX: "Fundamentals of Applied Sciences" - audit for free'])}
- {random.choice(['Khan Academy: Great for foundational concepts', 'Udemy: "Complete Guide to Professional Applications" - often on sale for ₹499', 'GitHub: Repository of practical examples and code', 'ResearchGate: Papers and discussions on advanced topics'])}

**Christ University Resources:**
- Knowledge Portal: Check the "Additional Resources" section uploaded by {random.choice(professor_names)}
- Library Database: Access to {random.choice(['IEEE papers', 'Harvard Business Review', 'JSTOR articles', 'SpringerLink journals', 'Oxford Academic publications'])}
- Previous Year Materials: Available in the department library archive
- Study Group Resources: Shared in our {random.choice(['Microsoft Teams channel', 'Google Drive folder', 'departmental WhatsApp group', 'class resource repository'])}

I found these particularly helpful for {random.choice(['understanding the theoretical concepts', 'preparing for practical applications', 'solving complex problems', 'visualizing abstract ideas', 'connecting concepts across different units'])}.

Hope these help! Feel free to add more resources in the comments."""
    
    else:
        content = f"""Wanted to start a conversation about {title.lower().replace('?', '')}.

My experience so far has been {random.choice(['very positive', 'somewhat mixed', 'challenging but rewarding', 'different than expected', 'quite interesting'])}.

Some observations:
- {random.choice(['The faculty is generally helpful and knowledgeable', 'Course content is comprehensive but demanding', 'Campus facilities are excellent but sometimes crowded', 'Administrative processes could be more streamlined', 'Extra-curricular options are diverse and enriching'])}
- {random.choice(['The workload can be intense, especially around assessment periods', 'Opportunities for practical application vary between courses', 'Peer collaboration is encouraged but competitive', 'Industry connections are valuable for placements', 'Research support depends significantly on your department and faculty'])}
- {random.choice(['Balancing academics with other activities requires careful planning', 'Building good relationships with professors makes a big difference', 'Taking initiative for projects beyond curriculum is appreciated', 'Interdisciplinary exposure is available but requires effort', 'Alumni network can be very helpful for career guidance'])}

I'm curious to know how others are finding their experience, especially {random.choice(['those in different departments', 'senior students who have more perspective', 'students who transferred from other universities', 'those balancing academics with other commitments', 'international students or those from other states'])}.

What are your thoughts? Any tips or insights to share?"""
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    updated_at = get_random_date(created_at, datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "subreddit_id": subreddit_id,
        "creator_id": str(creator_id),
        "title": title,
        "content": content,
        "type": thread_type,
        "created_at": created_at,
        "updated_at": updated_at,
        "tags": random.sample(["help", "question", "discussion", "project", "resource", "debate", "advice", "showcase", "academics", "campus", "careers", "events"], random.randint(1, 3)),
        "upvotes": random.randint(0, 30),
        "downvotes": random.randint(0, 10)
    }

def generate_comment_sample(thread_id, author_id, parent_id=None, thread_title=None):
    """Generate a sample comment document with Christ University specific context"""
    
    # Extract context from thread title if available
    context_words = []
    if thread_title:
        context_words = [word.lower() for word in thread_title.split() if len(word) > 3]
    
    # Christ University specific templates
    christ_specific_templates = [
        "As a {year} {department} student at Christ, I've found that {advice}. Have you tried {suggestion}?",
        "From my experience at Christ {campus}, {experience}. This might help with your {issue}.",
        "Prof. {professor} mentioned in class that {insight}. That could be relevant to your question.",
        "I faced a similar situation in my {course_code} course. What worked for me was {solution}.",
        "The {resource} at Christ is really helpful for this. They offer {service} that could address your needs.",
        "Last semester in {department}, we had to {task} and I found that {approach} was most effective.",
        "According to the Christ University guidelines, {policy}. However, {alternative} might be worth considering.",
        "During {event} last year, I learned that {learning}. Maybe that perspective could help you."
    ]
    
    # Generic comment templates
    generic_templates = [
        "I think {opinion} because {reason}. Have you considered {suggestion}?",
        "Based on my experience, {experience}. This might help with your {issue}.",
        "Great question! {answer} Hope that helps.",
        "I disagree with {point}. Instead, {alternative} would be more effective.",
        "Thanks for sharing! I've been working on something similar and found that {finding}.",
        "Have you tried {approach}? It worked well for me when I was dealing with {similar_problem}.",
        "This is actually a common issue in {field}. The standard solution is to {solution}.",
        "I'd recommend {recommendation}. It made a huge difference in my own projects."
    ]
    
    # Choose between Christ-specific and generic templates based on context
    if context_words and random.random() < 0.7:
        template = random.choice(christ_specific_templates)
    else:
        template = random.choice(generic_templates)
    
    # Christ University specific fillers
    fillers = {
        "year": ["first-year", "second-year", "third-year", "final-year", "Masters", "PhD"],
        "department": ["Computer Science", "Data Science", "Business Administration", "Law", "Psychology", "English Literature", "Economics", "Engineering"],
        "campus": ["Main Campus", "BGR Campus", "Kengeri Campus", "Lavasa Campus", "Delhi NCR Campus", "Yeshwanthpur Campus"],
        "professor": ["Sharma", "Patel", "Mehta", "Reddy", "Singh", "Thomas", "Kumar", "Joshi", "Bhat", "Rao", "Nair", "Menon"],
        "course_code": ["CSC301", "BUS405", "LAW220", "ENG389", "MED456", "PSY331", "DSC270", "ECO180", "MAT215"],
        "resource": ["Knowledge Centre", "Central Library", "Research Cell", "Student Welfare Office", "Placement Cell", "Departmental Lab", "Career Guidance Cell", "Centre for Academic Excellence"],
        "service": ["one-on-one consultations", "workshops", "resource materials", "peer mentoring", "expert sessions", "practical laboratories", "interactive sessions", "consultation hours"],
        "event": ["Blossoms Festival", "In-Bloom Tech Fest", "Management Conclave", "Literary Week", "Research Day", "Industrial Visit", "Annual Sports Meet", "Alumni Connect"],
        
        # Generic fillers (some with Christ University context)
        "advice": ["focusing on practical applications really helps master the theory", "maintaining consistent study habits is key", "forming study groups with diverse perspectives enhances learning", "balancing academics with co-curriculars makes for a better experience", "taking advantage of faculty consultation hours makes a huge difference"],
        "suggestion": ["reviewing past question papers from the Knowledge Centre", "attending the workshops organized by the department", "connecting with seniors who've taken the course", "using the additional resources on Knowledge Pro", "scheduling regular group study sessions"],
        "experience": ["the courses require consistent effort rather than last-minute cramming", "building good relationships with professors opens many opportunities", "participating in department events helps build practical knowledge", "volunteering for organizing committee positions develops valuable skills", "maintaining a good attendance record gives you flexibility when you really need it"],
        "issue": ["assignment deadlines", "complex concepts", "project management", "exam preparation", "balancing multiple commitments", "research methodology", "technical implementation"],
        "insight": ["connecting theory with real-world applications is crucial", "understanding the fundamentals thoroughly makes advanced topics easier", "industry perspective adds valuable context to academic knowledge", "interdisciplinary approaches often yield the most innovative solutions", "research skills are valuable regardless of your career path"],
        "solution": ["breaking down the project into manageable milestones", "focusing on understanding concepts rather than memorizing", "consulting additional resources beyond the prescribed textbook", "forming a study group with complementary skills", "creating visual maps to connect different concepts"],
        "task": ["complete a major project", "prepare for comprehensive exams", "deliver a team presentation", "write a research paper", "develop a practical solution", "analyze complex case studies"],
        "approach": ["starting early and spacing out the work", "collaborating with peers from different specializations", "consulting multiple sources for a broader perspective", "focusing on practical applications of theoretical concepts", "getting regular feedback from professors"],
        "policy": ["attendance below 85% makes you ineligible for exams", "all assignments must be submitted through the portal", "lab records need to be updated weekly", "project submissions require both digital and physical copies", "internal assessments contribute 50% to the final grade"],
        "alternative": ["speaking directly with your department coordinator might help", "applying for special consideration with proper documentation", "looking into the exception clauses in the student handbook", "seeking support from the Student Welfare Office", "discussing your specific situation with the Dean"],
        "learning": ["early preparation makes a significant difference", "collaborative approaches often yield better results", "practical experience complements theoretical knowledge", "seeking guidance proactively resolves many issues", "interdisciplinary knowledge creates unique advantages"],
        
        "opinion": ["the approach suggested in the lecture works best", "starting with the basics before advanced concepts is crucial", "practical implementation helps solidify theoretical understanding", "consistent small efforts work better than cramming", "interdisciplinary perspectives enhance problem-solving"],
        "reason": ["it builds a strong foundation", "it aligns with how assessments are structured", "it prepares you better for practical applications", "it's been consistently effective for most students", "it addresses both theoretical and practical aspects"],
        "point": ["focusing solely on textbook material", "leaving assignments until the last minute", "studying in isolation", "memorizing without understanding", "skipping the supplementary readings"],
        "alternative": ["active learning through problem-solving", "creating study groups with diverse perspectives", "connecting concepts across different modules", "seeking practical applications for theoretical concepts", "utilizing multimedia resources for complex topics"],
        "finding": ["consistent practice significantly improves understanding", "visual mapping of concepts helps retention", "teaching concepts to others solidifies your own understanding", "connecting theory to real-world examples enhances learning", "breaking complex topics into manageable chunks works well"],
        "approach": ["the Cornell note-taking method", "spaced repetition for concept retention", "creating mind maps for complex topics", "practice tests under timed conditions", "explaining concepts to someone else"],
        "similar_problem": ["understanding abstract concepts", "managing multiple assignment deadlines", "preparing for cumulative exams", "balancing depth and breadth in research", "coordinating group projects effectively"],
        "field": ["academic research", "project management", "technical implementation", "theoretical frameworks", "data analysis", "experimental design"],
        "solution": ["break it down into manageable components", "focus on understanding the underlying principles", "create a structured study plan", "seek multiple perspectives on the problem", "use visual aids to organize complex information"],
        "recommendation": ["the supplementary materials on the Knowledge Portal", "forming a study group with complementary strengths", "the workshop series organized by the department", "scheduling regular consultations with teaching assistants", "the reference books available in the Christ library"]
    }
    
    # Add Christ University specific context if thread title contains relevant keywords
    if context_words:
        relevant_context = None
        for word in context_words:
            if word in ["exam", "test", "assessment", "cia"]:
                relevant_context = "Make sure to check the exam schedule on Knowledge Pro - Christ University often updates it a week before CIA/ESE periods. Also, review the blue books from previous semesters in the department library."
            elif word in ["project", "assignment", "submission"]:
                relevant_context = "Remember that Christ University is strict about plagiarism checks through Turnitin. Keep your similarity index below 15% to avoid issues with your submission."
            elif word in ["placement", "internship", "job", "career"]:
                relevant_context = "The Center for Placements and Career Guidance (CPCG) at Christ offers excellent resources. Their portal lists opportunities specifically for Christ students that aren't available on public job sites."
            elif word in ["attendance", "absence", "leave"]:
                relevant_context = "Just to add to this discussion - Christ University's attendance policy requires 85% attendance to be eligible for end semester exams. Medical leave requires proper documentation submitted within 3 days."
            elif word in ["hostel", "accommodation", "housing"]:
                relevant_context = "If you're looking for off-campus housing, check the Christ University Student Welfare Office's verified PG list. They maintain contacts with approved accommodations near all campuses."
                
        if relevant_context and random.random() < 0.7:
            template += f" {relevant_context}"
    
    # Replace placeholders with relevant content
    for placeholder in fillers:
        if "{" + placeholder + "}" in template:
            template = template.replace("{" + placeholder + "}", random.choice(fillers[placeholder]))
    
    content = template
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "thread_id": thread_id,
        "parent_id": parent_id,
        "author_id": str(author_id),
        "content": content,
        "created_at": created_at,
        "upvotes": random.randint(0, 15),
        "downvotes": random.randint(0, 5),
        "is_answer": random.random() < 0.2 if parent_id is None else False  # Only top-level comments can be answers, and only some are
    }

def generate_study_spot_sample(creator_id=None):
    """Generate a sample study spot document near Christ University"""
    
    # Christ University campus options
    campus_options = [
        "Christ University Main Campus", 
        "Christ University Kengeri Campus", 
        "Christ University BGR Campus",
        "Christ University Yeshwanthpur Campus", 
        "Christ University School of Business", 
        "Christ University School of Law"
    ]
    campus = random.choice(campus_options)
    
    # Buildings and areas specific to Christ University and surrounding areas
    building_options = {
        "Christ University Main Campus": [
            "Central Library", "Knowledge Centre", "Block I", "Block II", "Block III", 
            "Block IV", "Science Block", "MBA Block", "Cafeteria", "Quadrangle"
        ],
        "Christ University Kengeri Campus": [
            "Main Library", "Central Block", "Engineering Block", "Architecture Block", 
            "Food Court", "Indoor Stadium", "Research Center", "Innovation Hub"
        ],
        "Christ University BGR Campus": [
            "Academic Block", "Central Library", "IT Center", "MBA Building", 
            "Law School Building", "Student Centre", "Research Wing", "Cafeteria"
        ],
        "Christ University Yeshwanthpur Campus": [
            "Main Block", "Library", "Labs Wing", "Student Lounge", 
            "Research Center", "Conference Hall", "Design Studio", "Food Court"
        ],
        "Christ University School of Business": [
            "MBA Block", "Library", "Case Study Room", "Seminar Hall", 
            "Computer Lab", "Business Incubation Centre", "Bloomberg Lab", "Student Lounge"
        ],
        "Christ University School of Law": [
            "Law Library", "Moot Court", "Seminar Hall", "Computer Lab", 
            "Research Wing", "Legal Aid Centre", "Conference Room", "Student Common Room"
        ]
    }
    
    # Nearby off-campus study spots
    off_campus_options = {
        "Christ University Main Campus": [
            "Brigade Road Starbucks", "Church Street Social", "Cubbon Park", 
            "Indian Coffee House", "Third Wave Coffee Roasters", "WeWork Galaxy"
        ],
        "Christ University Kengeri Campus": [
            "Coffee Day", "Kengeri Public Library", "Metro Station Lounge", 
            "Tata Starbucks", "Local Study Centre", "24/7 Study Cafe"
        ],
        "Christ University BGR Campus": [
            "Bannerghatta Road Cafe Coffee Day", "Gopalan Mall Food Court", 
            "Chai Point", "WeWork Varthur", "Third Wave Coffee", "Study Lounge Cafe"
        ],
        "Christ University Yeshwanthpur Campus": [
            "Orion Mall Food Court", "Coffee Day Orion", "Yeshwanthpur Public Library", 
            "Metro Station Workspace", "Starbucks Goreguntepalya", "Cafe Azzure"
        ],
        "Christ University School of Business": [
            "Coffee Day J P Nagar", "Forum Mall Work Space", "Third Wave JP Nagar", 
            "WeWork Embassy", "The Square Cafe", "Study Hub"
        ],
        "Christ University School of Law": [
            "Koramangala Social", "WeWork Koramangala", "Tea Trails", 
            "Starbucks 80 Feet Road", "Atta Galatta", "Third Wave Coffee HSR"
        ]
    }
    
    # Decide between on-campus and off-campus (70% on-campus, 30% off-campus)
    is_on_campus = random.random() < 0.7
    
    if is_on_campus:
        building_list = building_options.get(campus, ["Main Building"])
        building = random.choice(building_list)
        
        area_options = [
            "1st Floor", "2nd Floor", "3rd Floor", "Ground Floor", "Basement", 
            "Reading Room", "Quiet Zone", "Group Study Area", "Computer Lab", 
            "Research Section", "Journal Section", "Reference Section", "Study Carrels"
        ]
        area = random.choice(area_options)
        
        name = f"{campus} - {building} - {area}"
        address = f"{building}, {campus}, Bangalore"
    else:
        # Off-campus location
        off_campus_list = off_campus_options.get(campus, ["Local Coffee Shop"])
        building = random.choice(off_campus_list)
        
        areas = [
            "Quiet Corner", "Upper Floor", "Window Seating", "Outdoor Patio", 
            "Group Tables", "Work Pods", "Study Area", "Main Area", "Lounge Seating"
        ]
        area = random.choice(areas)
        
        name = f"{building} - {area}"
        address = f"Near {campus}, Bangalore"
    
    description_templates = [
        "A {atmosphere} study spot with {features}. {recommendation}",
        "This {area_type} offers {amenities}. {best_for}",
        "Popular for {activities}, this spot has {positive_aspects} but {negative_aspects}.",
        "A {time_of_day} favorite with {unique_feature}. {insider_tip}",
        "This {size} space is known for {known_for}. {additional_info}"
    ]
    
    fillers = {
        "atmosphere": ["quiet", "bustling", "cozy", "spacious", "modern", "academic", "bright", "secluded"],
        "features": [
            "comfortable seating and natural lighting",
            "plenty of outlets and fast Wi-Fi",
            "individual study carrels and group tables",
            "whiteboard walls and projector screens",
            "adjustable standing desks and ergonomic chairs",
            "air conditioning and good lighting",
            "reference materials and computer access",
            "proximity to the cafeteria for quick breaks"
        ],
        "recommendation": [
            "Perfect for long study sessions before Christ University exams.",
            "Great for focusing on CIA preparation.",
            "Ideal for group projects and Christ University assignments discussions.",
            "Excellent for creative work and brainstorming for Christ events.",
            "Best during morning hours when most Christ students have classes.",
            "Popular among senior students preparing for placement interviews.",
            "Convenient for quick study sessions between Christ University lectures."
        ],
        "area_type": ["study lounge", "library section", "collaborative space", "computer lab", "reading room", "quiet zone", "research area"],
        "amenities": [
            "fast internet, comfortable seating, and nearby restrooms",
            "charging stations, vending machines, and adjustable lighting",
            "large tables, private booths, and bookable rooms",
            "dual-monitor workstations, printing services, and technical support",
            "soundproof rooms, presentation equipment, and reservable spaces",
            "access to academic journals, reference books, and online databases",
            "climate control, water dispensers, and proximity to refreshments"
        ],
        "best_for": [
            "Best for individual study and research for Christ University coursework.",
            "Perfect for coding sessions and technical projects for CS department.",
            "Ideal for reading and note-taking for literature courses.",
            "Great for team collaboration and MBA project work.",
            "Excellent for students who need a distraction-free environment before exams.",
            "Optimal for law students preparing case briefs and presentations.",
            "Suitable for data science students working on computational projects."
        ],
        "activities": ["group study", "individual work", "research", "project collaboration", "exam preparation", "assignment completion", "online classes", "tutorial sessions"],
        "positive_aspects": [
            "excellent lighting and comfortable furniture",
            "quiet atmosphere and minimal distractions",
            "convenient location and extended hours",
            "helpful staff and useful resources",
            "modern technology and reliable internet",
            "proximity to Christ University and accessible by public transport",
            "good security and safe environment even late hours"
        ],
        "negative_aspects": [
            "can get crowded during CIA and ESE periods",
            "limited food options nearby",
            "temperature can be inconsistent",
            "occasional noise from nearby areas",
            "limited availability during peak hours",
            "closes early on weekends",
            "Wi-Fi can be slow during peak usage times"
        ],
        "time_of_day": ["morning", "afternoon", "evening", "late-night", "weekend", "weekday"],
        "unique_feature": [
            "floor-to-ceiling windows overlooking campus",
            "private study pods with sound dampening",
            "built-in dual monitor setups at each desk",
            "adjustable lighting for different study needs",
            "proximity to the campus cafe for coffee breaks",
            "special reference section for Christ University courses",
            "24/7 access with Christ University ID card"
        ],
        "insider_tip": [
            "Pro tip: The corner desks have the best power outlet access and natural lighting.",
            "Hidden gem: Few Christ students know about this location, so it's rarely full even during exam week.",
            "Insider advice: Bring a sweater as it gets cold in the afternoons due to strong AC.",
            "Local secret: The vending machines here are stocked more frequently than others on campus.",
            "Regular's insight: Tuesday mornings are the least crowded time to secure the best spots.",
            "Student hack: You can reserve study rooms 48 hours in advance through the Christ University portal.",
            "Christ veteran tip: This spot has the fastest Wi-Fi connection compared to other areas on campus."
        ],
        "size": ["intimate", "mid-sized", "spacious", "compact", "expansive", "multi-level"],
        "known_for": [
            "its pin-drop silence policy perfect for serious studying",
            "the beautiful architecture and inspiring design",
            "being open later than other campus locations",
            "having the fastest Wi-Fi on campus",
            "its comfortable lounge areas for relaxed studying",
            "being the preferred spot for Christ University toppers",
            "excellent natural lighting that reduces eye strain during long study sessions"
        ],
        "additional_info": [
            "Reservations recommended for group study rooms through the Christ University portal.",
            "Bring your Christ student ID for after-hours access and printing services.",
            "The nearby cafe offers student discounts with valid Christ University ID.",
            "Visit their website for real-time occupancy information before coming.",
            "Staff can help with technical equipment if needed for presentations.",
            "Special extended hours during examination periods for Christ University students.",
            "Regular workshops and study groups are hosted here for various Christ University courses."
        ]
    }
    
    template = random.choice(description_templates)
    for placeholder in [p for p in fillers.keys() if "{"+p+"}" in template]:
        template = template.replace("{"+placeholder+"}", random.choice(fillers[placeholder]))
    
    description = template
    
    amenities = {
        "wifi": random.choice([True, True, True, False]),  # Higher chance of having WiFi
        "outlets": random.choice([True, True, False]),
        "quiet": random.choice([True, False]),
        "group_friendly": random.choice([True, False]),
        "food_allowed": random.choice([True, False]),
        "computers": random.choice([True, False, False]),  # Lower chance of having computers
        "printing": random.choice([True, False, False]),
        "reservable": random.choice([True, False]),
        "whiteboard": random.choice([True, False]),
        "natural_light": random.choice([True, False])
    }
    
    # Generate coordinates for Bangalore (where Christ University is located)
    # Christ University Main Campus approximate coordinates
    base_lat, base_lng = 12.9344, 77.6069
    
    # Adjust based on campus
    if "Kengeri" in campus:
        base_lat, base_lng = 12.9102, 77.4826
    elif "BGR" in campus or "Bannerghatta" in campus:
        base_lat, base_lng = 12.8687, 77.5957
    elif "Yeshwanthpur" in campus:
        base_lat, base_lng = 13.0243, 77.5538
    
    # Add slight variation
    lat = base_lat + random.uniform(-0.008, 0.008)
    lng = base_lng + random.uniform(-0.008, 0.008)
    
    return {
        "_id": ObjectId(),
        "name": name,
        "location": {
            "type": "Point",
            "coordinates": [lng, lat]  # [longitude, latitude]
        },
        "address": address,
        "description": description,
        "amenities": amenities,
        "photos": [f"/static/studyspots/spot_{random.randint(1000, 9999)}.jpg" for _ in range(random.randint(1, 3))],
        "verified": random.choice([True, False, True]),  # Higher chance of being verified
        "created_by": str(creator_id) if creator_id else None,
        "created_at": get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    }

def generate_occupancy_report_sample(spot_id, user_id):
    """Generate a sample occupancy report document"""
    occupancy_level = random.choice(["low", "medium", "high"])
    reported_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "spot_id": spot_id,
        "user_id": str(user_id),
        "occupancy_level": occupancy_level,
        "reported_at": reported_at
    }

def generate_check_in_sample(spot_id, user_id):
    """Generate a sample check-in document"""
    check_in_time = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    duration = random.randint(1, 5)  # Hours
    check_out_time = check_in_time + timedelta(hours=duration)
    
    return {
        "_id": ObjectId(),
        "spot_id": spot_id,
        "user_id": str(user_id),
        "check_in_time": check_in_time,
        "check_out_time": check_out_time
    }

def generate_tutor_profile_sample(user_id, user_data):
    """Generate a sample tutor profile document for Christ University students"""
    # Use user's department to determine subjects they can tutor
    department = user_data.get("department", "General")
    
    # Christ University specific subjects
    subjects_by_department = {
        "Computer Science": ["Programming Fundamentals", "Data Structures & Algorithms", "Database Systems", "Web Technologies", "Python Programming", "Java Programming", "Computer Networks", "Operating Systems", "Software Engineering", "Mobile App Development"],
        "Data Science": ["Statistical Methods", "Data Analysis with Python", "Machine Learning", "Data Visualization", "Big Data Analytics", "Predictive Modeling", "SQL for Data Science", "Time Series Analysis", "Text Mining", "Business Intelligence"],
        "Artificial Intelligence": ["Machine Learning Algorithms", "Neural Networks", "Computer Vision", "Natural Language Processing", "Reinforcement Learning", "AI Ethics", "Deep Learning", "Robotics", "Pattern Recognition", "Cognitive Computing"],
        "Business Administration": ["Principles of Management", "Marketing Management", "Financial Accounting", "Organizational Behavior", "Business Economics", "Business Communication", "Human Resource Management", "Strategic Management", "Project Management", "Operations Management"],
        "Economics": ["Microeconomics", "Macroeconomics", "Economic Development", "Public Economics", "International Economics", "Econometrics", "Financial Economics", "Labor Economics", "Industrial Economics", "Environmental Economics"],
        "Finance": ["Corporate Finance", "Investment Analysis", "Financial Management", "Banking Operations", "Security Analysis", "Portfolio Management", "Risk Management", "Financial Markets", "Taxation", "Financial Accounting"],
        "Marketing": ["Marketing Principles", "Consumer Behavior", "Digital Marketing", "Market Research", "Brand Management", "Advertising & Promotion", "Retail Management", "Services Marketing", "B2B Marketing", "Global Marketing"],
        "Psychology": ["General Psychology", "Social Psychology", "Developmental Psychology", "Cognitive Psychology", "Clinical Psychology", "Personality Theory", "Psychological Testing", "Counseling Psychology", "Abnormal Psychology", "Educational Psychology"],
        "English Literature": ["Literary Theory", "Creative Writing", "Shakespeare Studies", "American Literature", "British Literature", "Indian Writing in English", "Postcolonial Literature", "Critical Analysis", "Academic Writing", "Poetry Analysis"],
        "History": ["Indian History", "World History", "Ancient Civilizations", "Medieval History", "Modern History", "Contemporary History", "Historical Methods", "Cultural History", "Political History", "Social History"],
        "Political Science": ["Political Theory", "Indian Constitution", "International Relations", "Comparative Politics", "Public Administration", "Political Ideology", "Foreign Policy", "Human Rights", "Diplomacy", "Political Sociology"],
        "Law": ["Constitutional Law", "Contract Law", "Criminal Law", "Corporate Law", "Intellectual Property Law", "International Law", "Family Law", "Property Law", "Environmental Law", "Legal Writing"]
    }
    
    # Default to general subjects if department not found
    subjects = subjects_by_department.get(department, ["Study Skills", "Academic Writing", "Research Methods", "Critical Thinking", "Presentation Skills", "Time Management", "Exam Preparation", "Note-Taking Techniques"])
    
    # Select 2-5 subjects
    tutoring_subjects = random.sample(subjects, min(random.randint(2, 5), len(subjects)))
    
    # Generate bio with Christ University focus
    bio_templates = [
        "{year} {department} student at Christ University offering tutoring in {subjects}. {experience} {teaching_style}",
        "Experienced Christ University tutor specializing in {subjects}. {background} {approach}",
        "Passionate about teaching {subjects} to fellow Christ students. {qualification} {philosophy}",
        "Christ University {department} enthusiast with a knack for explaining complex concepts. {strength} {goal}",
        "Dedicated Christ University tutor with expertise in {subjects}. {method} {benefit}"
    ]
    
    fillers = {
        "year": user_data.get("year", "Current"),
        "department": department,
        "subjects": " and ".join(tutoring_subjects),
        "experience": [
            "I've been tutoring for over 2 years at Christ University.",
            "I've helped dozens of Christ students improve their grades in these subjects.",
            "I work as a Teaching Assistant for introductory courses at Christ.",
            "I've developed study materials that simplify complex topics for Christ University courses.",
            "I've consistently received excellent feedback from previous Christ University students.",
            "I've conducted workshop sessions for multiple batches at Christ University.",
            "I maintain a CGPA of 3.8+ in these subjects at Christ University."
        ],
        "teaching_style": [
            "My teaching style focuses on building intuition rather than memorization, which is crucial for Christ University exams.",
            "I believe in personalized approaches tailored to each student's learning style, especially for Christ University's diverse course structure.",
            "I emphasize practical applications alongside theoretical understanding, which helps with Christ's practical components.",
            "I break down complex topics into manageable pieces, perfect for Christ University's rigorous curriculum.",
            "I use real-world examples to make abstract concepts more concrete, which helps with application questions in Christ University exams.",
            "I create custom study materials aligned with Christ University's syllabus and examination patterns.",
            "I focus on examination strategies specific to Christ University's evaluation methods."
        ],
        "background": [
            "I maintain a 3.9+ GPA in my major courses at Christ University.",
            "I've worked on research projects with Christ University faculty.",
            "I've won academic competitions representing Christ University.",
            "I've completed advanced coursework beyond my current level at Christ.",
            "I have industry experience that complements my academic knowledge from Christ University.",
            "I've been recognized for academic excellence in my department at Christ University.",
            "I've participated in national-level competitions representing Christ University."
        ],
        "approach": [
            "I adapt my teaching methods to match your learning style while ensuring alignment with Christ University's requirements.",
            "I focus on building a strong conceptual foundation before diving into advanced topics, which is essential for Christ's comprehensive exams.",
            "I emphasize problem-solving strategies aligned with Christ University's examination patterns.",
            "I provide comprehensive study materials tailored to specific Christ University courses.",
            "I assign practice problems that reinforce key concepts between sessions, designed to mirror Christ University's assessment style.",
            "I structure sessions to gradually build confidence for tackling Christ University's challenging assessments.",
            "I incorporate previous years' question papers from Christ University to guide our preparation strategy."
        ],
        "qualification": [
            "I've received top marks in all these subjects at Christ University.",
            "I've been recognized for academic excellence in my department at Christ.",
            "I've taken advanced electives in these areas at Christ University.",
            "I've served as a research assistant in this field at Christ University.",
            "I've participated in specialized training programs for these subjects through Christ University.",
            "I've been selected as a peer mentor for these courses at Christ University.",
            "I've won departmental awards for excellence in these subjects at Christ University."
        ],
        "philosophy": [
            "I believe everyone can master these subjects with the right guidance, especially the way they're taught at Christ University.",
            "My goal is to help you develop independent learning skills that will serve you throughout your academic journey at Christ.",
            "I focus on building confidence alongside competence, crucial for success in Christ University's challenging programs.",
            "I strive to make learning enjoyable, not just effective, even for the most demanding Christ University courses.",
            "I tailor my approach to address your specific challenges in Christ University's curriculum.",
            "I aim to develop a comprehensive understanding that goes beyond just scoring well in Christ University exams.",
            "I believe in creating a supportive learning environment that alleviates the stress of Christ University's rigorous academics."
        ],
        "strength": [
            "I excel at explaining complex concepts in simple terms, which is particularly helpful for Christ University's detailed syllabus.",
            "My strength is identifying and addressing knowledge gaps quickly in Christ University's cumulative curriculum.",
            "I'm particularly good at helping students overcome learning plateaus in challenging Christ University courses.",
            "I have a talent for creating memorable explanations and examples relevant to Christ University's examination patterns.",
            "I'm skilled at adapting material to different learning preferences while covering all essential concepts in Christ's curriculum.",
            "I can clearly explain complex theoretical frameworks in ways that connect to Christ University's practical components.",
            "I'm adept at creating structured study plans that ensure complete coverage of Christ University's extensive syllabus."
        ],
        "goal": [
            "My goal is to help you not just pass, but truly excel in your Christ University courses.",
            "I aim to help you develop study skills that will serve you throughout your academic career at Christ University.",
            "I want to help you build confidence in your abilities in these challenging subjects at Christ.",
            "My mission is to make these subjects accessible and even enjoyable, despite Christ University's rigorous standards.",
            "I focus on helping you connect theoretical knowledge with practical applications, essential for Christ's holistic assessment.",
            "I strive to transform these subjects from challenging obstacles to your areas of strength at Christ University.",
            "My aim is to help you develop independent learning strategies effective within Christ University's academic framework."
        ],
        "method": [
            "I use a step-by-step approach that builds from fundamentals to advanced concepts, aligned with Christ University's teaching methodology.",
            "I incorporate visual aids, diagrams, and models to explain abstract ideas, making Christ University's complex topics accessible.",
            "I assign targeted practice problems that reinforce key concepts and prepare you for Christ's assessment patterns.",
            "I provide detailed feedback and personalized study strategies based on Christ University's evaluation criteria.",
            "I use analogies and real-world examples to make difficult concepts relatable, connecting theory to application in Christ's curriculum.",
            "I create custom study materials that complement Christ University's resources and address common areas of difficulty.",
            "I implement active learning strategies that ensure engagement with Christ University's comprehensive content."
        ],
        "benefit": [
            "Christ University students often report significant grade improvements after just a few sessions.",
            "My tutees consistently report increased confidence in handling Christ University's challenging assessments.",
            "Previous students have gone on to excel in advanced Christ University courses in these subjects.",
            "My approach helps develop critical thinking skills that extend beyond the classroom, essential for Christ's holistic education.",
            "Working with me will help you build a solid foundation for future academic success at Christ University.",
            "Students appreciate my ability to make even the most complex aspects of Christ University's curriculum manageable.",
            "My students consistently perform above the class average in Christ University's continuous and end-semester examinations."
        ]
    }
    
    bio_template = random.choice(bio_templates)
    for placeholder in [p for p in fillers.keys() if "{"+p+"}" in bio_template]:
        if isinstance(fillers[placeholder], list):
            filler = random.choice(fillers[placeholder])
        else:
            filler = fillers[placeholder]
        bio_template = bio_template.replace("{"+placeholder+"}", filler)
    
    bio = bio_template
    
    # Generate hourly rate based on year of study
    year_to_rate = {
        "1st Year": lambda: random.randint(200, 350),  # Adjusted for INR
        "2nd Year": lambda: random.randint(300, 450),
        "3rd Year": lambda: random.randint(400, 550),
        "Final Year": lambda: random.randint(500, 650),
        "Masters": lambda: random.randint(600, 800),
        "PhD": lambda: random.randint(800, 1200)
    }
    
    year = user_data.get("year", "2nd Year")
    hourly_rate = year_to_rate.get(year, lambda: random.randint(350, 550))()
    
    # Generate availability
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    availability = {}
    
    # Randomly select 3-5 days of availability
    available_days = random.sample(days, random.randint(3, 5))
    
    for day in days:
        if day in available_days:
            # For available days, generate 1-3 time slots
            time_slots = []
            for _ in range(random.randint(1, 3)):
                start_hour, start_minute = get_random_time()
                end_hour = start_hour + random.randint(1, 3)  # 1-3 hour sessions
                if end_hour > 22:
                    end_hour = 22
                time_slots.append({
                    "start": f"{start_hour:02d}:{start_minute:02d}",
                    "end": f"{end_hour:02d}:{start_minute:02d}"
                })
            availability[day] = time_slots
        else:
            availability[day] = []
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "user_id": str(user_id),
        "subjects": tutoring_subjects,
        "hourly_rate": hourly_rate,
        "bio": bio,
        "availability": availability,
        "average_rating": round(random.uniform(3.5, 5.0), 1),  # Average rating between 3.5 and 5.0
        "created_at": created_at
    }

def generate_tutoring_session_sample(tutor_id, student_id, tutor_profile):
    """Generate a sample tutoring session document"""
    subject = random.choice(tutor_profile["subjects"])
    
    # Generate scheduled time based on tutor's availability
    availability = tutor_profile["availability"]
    available_days = [day for day, slots in availability.items() if slots]
    
    if not available_days:
        # Fallback if no availability data
        day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_hour = random.randint(9, 18)
        start_minute = random.choice([0, 30])
    else:
        day = random.choice(available_days)
        time_slot = random.choice(availability[day])
        start_time = time_slot["start"].split(":")
        start_hour = int(start_time[0])
        start_minute = int(start_time[1])
    
    # Generate a date for the selected day
    # First, find a date that corresponds to the chosen day of the week
    base_date = datetime(2023, 1, 1)
    days_ahead = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    day_num = days_ahead.get(day, 0)
    
    # Adjust base_date to match the desired day of the week
    while base_date.weekday() != day_num:
        base_date += timedelta(days=1)
    
    # Now randomly select a date with the same day of week within our date range
    max_weeks = 52  # Up to a year
    selected_week = random.randint(0, max_weeks)
    scheduled_date = base_date + timedelta(weeks=selected_week)
    
    # Combine date and time
    scheduled_time = scheduled_date.replace(hour=start_hour, minute=start_minute)
    
    # Session duration (in minutes)
    duration = random.choice([60, 90, 120])
    
    # Generate status based on scheduled time
    now = datetime(2023, 12, 31)  # End of our date range
    if scheduled_time > now:
        status = "scheduled"
    else:
        status = random.choice(["completed", "completed", "completed", "cancelled"])  # Higher chance of completion
    
    # Generate payment amount
    hourly_rate = tutor_profile["hourly_rate"]
    payment_amount = int(hourly_rate * (duration / 60))
    
    # Generate meeting link for online sessions
    meeting_platforms = ["Zoom", "Google Meet", "Microsoft Teams"]
    platform = random.choice(meeting_platforms)
    meeting_link = f"https://{platform.lower().replace(' ', '')}.com/meeting-id-{random.randint(10000000, 99999999)}"
    
    created_at = get_random_date(datetime(2023, 1, 1), scheduled_time - timedelta(days=1))
    
    # Add location information for in-person sessions (40% chance of in-person)
    is_in_person = random.random() < 0.4
    location = None
    
    if is_in_person:
        christ_locations = [
            "Christ University Main Campus Library",
            "Knowledge Centre, Block IV",
            "Central Block Study Area",
            "Christ University Cafeteria",
            "MBA Block Conference Room",
            "Christ University BGR Campus Library",
            "Christ University Kengeri Campus Study Centre",
            "Science Block Laboratory Wing",
            "Christ University Law Library",
            "Student Centre Meeting Room"
        ]
        location = random.choice(christ_locations)
    
    return {
        "_id": ObjectId(),
        "tutor_id": str(tutor_id),
        "student_id": str(student_id),
        "subject": subject,
        "scheduled_time": scheduled_time,
        "duration": duration,
        "status": status,
        "payment_amount": payment_amount,
        "meeting_link": None if is_in_person else meeting_link,
        "location": location,
        "is_in_person": is_in_person,
        "created_at": created_at
    }

def generate_tutor_review_sample(session_id, session_data):
    """Generate a sample tutor review document for Christ University"""
    if session_data["status"] != "completed":
        return None
    
    # Higher ratings on average (Christ University quality focus)
    rating = random.choices([3, 4, 5], weights=[1, 4, 7])[0]  # More weighted towards higher ratings
    
    # Christ University specific review templates
    review_templates = {
        3: [
            "The session was helpful for my {course} course, but could have been more comprehensive in covering Christ University's specific curriculum requirements. {positive}",
            "Decent tutoring for {course}, but sometimes moved too quickly through important concepts that are frequently tested in Christ University exams. {suggestion}",
            "Good knowledge of the subject, but the teaching style didn't always align with Christ University's teaching methodology. {improvement}",
            "Satisfactory session that helped with basics for my {course} at Christ. {mixed_feedback}",
            "Helped me understand some concepts for my Christ University {course} course, but I still have questions about examination-specific topics. {specific_feedback}"
        ],
        4: [
            "Very good session for my Christ University {course} course! {strength} {minor_issue}",
            "Knowledgeable tutor who explained concepts clearly in line with Christ University's curriculum. {positive_point}",
            "Great help with my {course} coursework at Christ. {specific_benefit} Will book again.",
            "Effective teaching style that made difficult concepts from Christ University's {course} easier to understand. {appreciation}",
            "Excellent explanations and patience with complex topics from my Christ {course} course. {positive_outcome} Just a bit rushed toward the end."
        ],
        5: [
            "Absolutely outstanding tutor for Christ University's challenging {course} course! {excellence} {result}",
            "Couldn't have asked for better help with my Christ University {course} assignments. {specific_excellence} Highly recommend!",
            "Exceptional knowledge and teaching ability specifically tailored to Christ University's {course} curriculum. {transformation} Will definitely book again!",
            "Perfect session that exceeded my expectations for {course} help. {specific_praise} Exactly what Christ University students need!",
            "Amazing tutor who went above and beyond in helping me with my Christ University {course} coursework. {detailed_excellence} 10/10!"
        ]
    }
    
    courses = [
        "CSC301", "CSC405", "DSC220", "AID389", "BUS456", 
        "LAW331", "ECO270", "FIN350", "PSY280", "ENG335", 
        "MKT420", "COM310", "POL250", "HIS215", "MAT380"
    ]
    
    fillers = {
        "course": random.choice(courses),
        "positive": [
            "The practice problems were useful for upcoming CIA tests.",
            "Good communication throughout and familiar with Christ University's grading system.",
            "Came prepared with materials related to our specific textbooks.",
            "Was patient with my questions about difficult topics in the Christ University syllabus.",
            "Provided some helpful resources for upcoming ESE preparation."
        ],
        "suggestion": [
            "Would benefit from more visual aids for complex concepts in Christ University's curriculum.",
            "Consider providing summary notes after sessions that align with examination patterns.",
            "Could use more real-world examples related to the Indian context as emphasized in our classes.",
            "Might help to check understanding more frequently, especially for topics prioritized in Christ University exams.",
            "Would appreciate more practice problems between sessions that match Christ University's question patterns."
        ],
        "improvement": [
            "Better preparation with Christ University's specific course materials would make sessions more effective.",
            "More interactive elements would improve engagement with challenging Christ University concepts.",
            "Could work on explaining fundamentals more clearly as taught in our lectures.",
            "Would benefit from more structured approach aligned with Christ University's teaching methodology.",
            "Consider adjusting pace based on student comprehension, especially for complex Christ University topics."
        ],
        "mixed_feedback": [
            "Strong on theory but could improve on practical applications as required by Christ University assessments.",
            "Explanations were clear but sometimes too brief for the depth required in Christ University exams.",
            "Good at answering questions but session lacked structure aligned with our course progression.",
            "Helpful but could be more engaging, especially for lengthy Christ University study sessions.",
            "Knowledgeable but occasionally assumed too much prior understanding of Christ University prerequisites."
        ],
        "specific_feedback": [
            "Needs to slow down when explaining complex topics that are crucial for Christ University examinations.",
            "Could provide more examples for difficult concepts that align with Christ University's question patterns.",
            "Would benefit from checking understanding more often, especially for common misconceptions in our course.",
            "Should provide more context for how topics connect to the broader Christ University curriculum.",
            "Would appreciate more focus on problem-solving strategies specific to Christ University's assessment style."
        ],
        "strength": [
            "Explained complex concepts in easy-to-understand ways using examples from our Christ University textbooks.",
            "Used excellent examples that clarified difficult topics frequently tested in Christ University exams.",
            "Was very patient with my questions on challenging Christ University course material.",
            "Provided helpful additional resources specifically designed for Christ University's curriculum.",
            "Structured the session effectively to maximize learning for upcoming Christ University assessments."
        ],
        "minor_issue": [
            "Could have spent a bit more time on practice problems typical in Christ University exams.",
            "Occasionally used terminology slightly different from what our professors use.",
            "Went slightly over our scheduled time, though it was to complete an important concept.",
            "Could improve on summary wrap-ups to consolidate learning before Christ University tests.",
            "Would appreciate more follow-up resources specific to Christ University's examination pattern."
        ],
        "positive_point": [
            "Appreciated the customized approach to my specific questions about Christ University assignments.",
            "The visual aids really helped cement my understanding of concepts frequently tested in CIA.",
            "I especially liked the real-world examples related to the Indian context as emphasized in our curriculum.",
            "The practice problems were perfectly targeted to the types of questions in Christ University exams.",
            "The session was well-structured with clear learning objectives aligned with our course outcomes."
        ],
        "specific_benefit": [
            "Helped me understand concepts I've been struggling with for weeks in my Christ University classes.",
            "My confidence in tackling Christ University's challenging assessments has significantly improved.",
            "I now have strategies to approach similar problems on my own in the upcoming semester exams.",
            "Cleared up misconceptions that were holding me back in understanding core Christ University concepts.",
            "Provided techniques that improved my studying efficiency for Christ University's comprehensive syllabus."
        ],
        "appreciation": [
            "Really appreciated the patience and thoroughness with Christ University's challenging material.",
            "Thankful for the additional examples beyond what's covered in our Christ University lectures.",
            "Valued the connections made to other course material in the Christ University curriculum.",
            "Grateful for the clear explanations and analogies that made complex Christ concepts accessible.",
            "Appreciated the follow-up resources shared after our session that align with Christ University's requirements."
        ],
        "positive_outcome": [
            "I feel much more confident about my upcoming CIA and ESE at Christ University.",
            "I'm now able to complete Christ University assignments independently with better understanding.",
            "My understanding of the subject has dramatically improved, which will reflect in my Christ University grades.",
            "I can now approach similar problems in Christ University exams with ease.",
            "I've already seen improvement in my coursework and class participation at Christ University."
        ],
        "excellence": [
            "Exceptional at breaking down complex concepts from Christ University's curriculum into understandable pieces.",
            "Remarkable ability to identify and address the gaps in my understanding of Christ University's challenging material.",
            "Outstanding at providing multiple perspectives on difficult topics in the Christ University syllabus.",
            "Incredible patience and clear communication throughout our session on complex Christ University concepts.",
            "Excellent preparation and personalized approach to my needs as a Christ University student."
        ],
        "result": [
            "I aced my CIA test after just one session!",
            "My understanding of the subject has completely transformed my performance in Christ University courses.",
            "I went from struggling to excelling in this topic for my Christ University assessments.",
            "Now I can solve problems that seemed impossible before in my Christ University assignments.",
            "My confidence in tackling Christ University's rigorous curriculum has skyrocketed."
        ],
        "specific_excellence": [
            "Explained concepts I've been struggling with in Christ University classes for months in ways that finally clicked.",
            "Created custom examples perfectly tailored to Christ University's curriculum and my learning style.",
            "Identified and fixed fundamental misconceptions I didn't even know I had about important Christ University course concepts.",
            "Provided a framework for approaching problems that has revolutionized my study approach for Christ University exams.",
            "Taught me strategies that have improved my performance across all my Christ University courses."
        ],
        "transformation": [
            "I went from failing to understanding everything in just one session, which will be crucial for my Christ University assessments.",
            "The concepts I've struggled with all semester in my Christ University course suddenly make perfect sense.",
            "My approach to problem-solving for Christ University assignments has completely changed for the better.",
            "I've gained an entirely new perspective on the subject as taught in the Christ University curriculum.",
            "My confidence in my academic abilities at Christ University has been completely restored."
        ],
        "specific_praise": [
            "The explanations were crystal clear, the examples were perfect for Christ University's curriculum, and the pace was just right.",
            "Every question was answered with incredible depth and clarity while remaining accessible to Christ University students.",
            "The session was perfectly structured, building from fundamentals to complex applications required in Christ University's curriculum.",
            "The patience, knowledge, and teaching skill demonstrated were truly exceptional for handling Christ University's challenging material.",
            "Not only addressed my immediate questions but strengthened my overall understanding of the Christ University course."
        ],
        "detailed_excellence": [
            "Prepared custom materials specifically for my needs in the Christ University curriculum, explained concepts with perfect clarity, and provided excellent follow-up resources.",
            "Used brilliant analogies that made abstract concepts concrete, identified my specific misconceptions about Christ University material, and provided targeted practice.",
            "Created a supportive learning environment, adjusted teaching approach to match my learning style, and went beyond the scheduled time to ensure I understood everything for my Christ University course.",
            "Combined deep subject knowledge with exceptional teaching ability, making even the most complex topics in Christ University's curriculum accessible and interesting.",
            "Demonstrated remarkable patience with my questions, explained concepts from multiple angles, and connected topics to the broader Christ University curriculum in illuminating ways."
        ]
    }
    
    template = random.choice(review_templates[rating])
    for placeholder in [p for p in fillers.keys() if "{"+p+"}" in template]:
        template = template.replace("{"+placeholder+"}", random.choice(fillers[placeholder]))
    
    review_text = template
    
    return {
        "_id": ObjectId(),
        "session_id": session_id,
        "tutor_id": session_data["tutor_id"],
        "student_id": session_data["student_id"],
        "rating": rating,
        "review_text": review_text,
        "created_at": session_data["scheduled_time"] + timedelta(hours=random.randint(1, 24))
    }

def generate_coin_transaction_sample(user_id, amount, transaction_type, reference_id=None):
    """Generate a sample coin transaction document"""
    descriptions = {
        "bounty_reward": ["Bounty reward for solving problem", "Reward for quality answer", "Bounty completion payment"],
        "bounty_posting": ["Cost to post bounty", "Bounty question fee", "Knowledge bounty posting"],
        "marketplace_sale": ["Sale of academic resource", "Payment for study material", "Revenue from marketplace listing"],
        "marketplace_purchase": ["Purchase of study material", "Payment for academic resource", "Marketplace item acquisition"],
        "tutoring_income": ["Tutoring session payment", "Income from tutoring", "Payment for academic assistance"],
        "tutoring_payment": ["Payment for tutoring services", "Tutor session fee", "Academic help payment"],
        "upvote_reward": ["Reward for upvoted content", "Community recognition bonus", "Quality contribution reward"],
        "system_bonus": ["Welcome bonus", "Activity milestone reward", "Weekly participation bonus"],
        "admin_adjustment": ["Manual balance adjustment", "Support team correction", "Administrative balance change"]
    }
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "user_id": str(user_id),
        "amount": amount,
        "transaction_type": transaction_type,
        "reference_id": str(reference_id) if reference_id else None,
        "description": random.choice(descriptions.get(transaction_type, ["Coin transaction"])),
        "created_at": created_at
    }

def generate_conversation_sample(participants):
    """Generate a sample conversation document"""
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    updated_at = get_random_date(created_at, datetime(2023, 12, 31))
    
    return {
        "_id": ObjectId(),
        "participants": [str(p) for p in participants],
        "created_at": created_at,
        "updated_at": updated_at
    }

def generate_message_sample(conversation_id, sender_id, recipient_ids):
    """Generate a sample message document with Christ University context"""
    christ_specific_templates = [
        "Hi! {christ_question}",
        "Thanks for your help with {christ_topic}. {christ_followup}",
        "I was wondering if you could {christ_request}?",
        "About our {christ_subject} {christ_context}.",
        "Just wanted to {christ_purpose}. {christ_details}"
    ]
    
    generic_templates = [
        "Hi! {question}",
        "Thanks for your help with {topic}. {followup}",
        "I was wondering if you could {request}?",
        "About our {subject} {context}.",
        "Just wanted to {purpose}. {details}"
    ]
    
    # Choose between Christ-specific and generic templates (70% chance of Christ-specific)
    if random.random() < 0.7:
        template = random.choice(christ_specific_templates)
    else:
        template = random.choice(generic_templates)
    
    fillers = {
        # Christ University specific questions
        "christ_question": [
            "Do you have time for a quick question about the Christ University CIA preparation?",
            "Could you clarify something from today's lecture at Christ Main Campus?",
            "Are you available for a study session this weekend at Christ Library?",
            "Do you know when Professor Sharma's office hours are at Christ BGR Campus?",
            "Would you be interested in forming a study group for the Christ University final exams?",
            "Have you registered for the Blossoms fest at Christ University yet?",
            "Did you understand the assignment requirements for CSC301 at Christ?",
            "Have you checked the updated Christ University exam schedule on Knowledge Pro?"
        ],
        "christ_topic": [
            "the Data Structures assignment from Professor Kumar",
            "the Management Theory project for Christ Business School",
            "explaining that concept from Christ University's AI course",
            "sharing your notes from the Christ University Constitutional Law lecture",
            "the practice problems from Christ University's Statistical Methods class",
            "the presentation for Christ University's In-Bloom Tech Fest",
            "the case study analysis for Christ MBA program",
            "the reference materials for Christ University's Research Methods course"
        ],
        "christ_followup": [
            "I understand it much better now and should be prepared for Christ University's assessment pattern.",
            "It really helped me prepare for the Christ University CIA exam.",
            "I was able to complete it on time because of you, despite Christ University's strict deadlines.",
            "Your explanation was much clearer than what we got in the Christ University lecture.",
            "I wouldn't have figured out Christ University's specific requirements without your assistance.",
            "Now I feel confident about the Christ University ESE pattern.",
            "I've incorporated your suggestions into my Christ University assignment submission.",
            "It made a big difference in understanding Christ University's grading criteria."
        ],
        "christ_request": [
            "help me with this week's problem set for Christ University's Algorithm Design course",
            "explain how to approach this type of question for Christ University's CIA pattern",
            "share your notes from yesterday's class at Christ Main Campus",
            "meet up to review for the Christ University midterm at Knowledge Centre",
            "recommend some additional resources for Christ University's Financial Accounting course",
            "help debug my project for Christ University's Web Development course",
            "give feedback on my presentation for Christ University's Management Conclave",
            "explain the Christ University grading system for practical components"
        ],
        "christ_subject": [
            "Christ University group project", "Christ Library study session", "Christ University tutorial", 
            "Christ University class notes", "upcoming Christ University exam", "Christ University internship fair",
            "Christ University Blossoms Festival participation", "Christ University placement preparation"
        ],
        "christ_context": [
            "I've finished my part and wanted to check if it meets Christ University guidelines",
            "I think we should focus on the chapters covered in Christ University's syllabus this week",
            "I found some helpful resources in Christ University's Knowledge Centre we could go through",
            "I've summarized the key points from Christ University's reference books we need to review",
            "I have a few questions about the approach as per Christ University's requirements",
            "I've booked a group study room at Christ University Main Campus Library",
            "I've collected sample papers from previous Christ University batches",
            "I've spoken to senior students at Christ University about important topics"
        ],
        "christ_purpose": [
            "check in about our Christ University assignment deadline",
            "confirm our meeting time tomorrow at Christ University Library",
            "share this helpful article relevant to our Christ University course",
            "ask about your approach to problem #5 in the Christ University practice set",
            "follow up on our discussion from Christ University's Data Structures class",
            "see if you're participating in Christ University's coding competition",
            "coordinate for the Christ University group presentation next week",
            "discuss the Christ University ESE preparation strategy"
        ],
        "christ_details": [
            "The professor mentioned specific formatting requirements for Christ University submissions.",
            "Is the Christ Library Central Block location still working for you?",
            "It covers topics that will be in the Christ University CIA next week.",
            "Would love to get your perspective before our Christ University viva.",
            "Just wanted to make sure we're on the same page regarding Christ University's expectations.",
            "The Christ University Academic Council has updated the assessment components.",
            "I heard Christ University might organize a workshop on this topic soon.",
            "The resources at Christ University Knowledge Centre would be helpful for this."
        ],
        
        # Generic messages (for diversity)
        "question": [
            "Do you have time for a quick question about the assignment?",
            "Could you clarify something from today's lecture?",
            "Are you available for a study session this weekend?",
            "Do you know when the professor's office hours are?",
            "Would you be interested in forming a study group for the final?"
        ],
        "topic": [
            "the last homework assignment",
            "the group project",
            "explaining that concept",
            "sharing your notes",
            "the practice problems"
        ],
        "followup": [
            "I understand it much better now.",
            "It really helped me prepare for the exam.",
            "I was able to complete it on time because of you.",
            "Your explanation was much clearer than the textbook.",
            "I wouldn't have figured it out without your assistance."
        ],
        "request": [
            "help me with this week's problem set",
            "explain how to approach this type of question",
            "share your notes from yesterday's class",
            "meet up to review for the midterm",
            "recommend some additional resources on this topic"
        ],
        "subject": [
            "group project", "study session", "tutorial", "class notes", "upcoming exam"
        ],
        "context": [
            "I've finished my part and wanted to check in",
            "I think we should focus on the chapters covered this week",
            "I found some helpful resources we could go through",
            "I've summarized the key points we need to review",
            "I have a few questions about the approach we're taking"
        ],
        "purpose": [
            "check in about our assignment deadline",
            "confirm our meeting time tomorrow",
            "share this helpful article I found",
            "ask about your approach to problem #5",
            "follow up on our discussion from class"
        ],
        "details": [
            "Let me know what you think.",
            "Is that still going to work for you?",
            "Hope it's helpful!",
            "Would love to get your perspective.",
            "Just wanted to make sure we're on the same page."
        ]
    }
    
    for placeholder in fillers:
        if "{"+placeholder+"}" in template:
            template = template.replace("{"+placeholder+"}", random.choice(fillers[placeholder]))
    
    content = template
    
    created_at = get_random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    # Randomly determine which recipients have read the message
    read_by = [str(sender_id)]  # Sender always "reads" their own message
    for recipient in recipient_ids:
        if random.random() > 0.3:  # 70% chance a recipient has read the message
            read_by.append(str(recipient))
    
    return {
        "_id": ObjectId(),
        "conversation_id": conversation_id,
        "sender_id": str(sender_id),
        "content": content,
        "read_by": read_by,
        "created_at": created_at
    }

# Database Setup: Main function
def setup_database():
    """Set up the MongoDB database for the INK platform with all collections and sample data"""
    reset_database()
    
    # Step 1: Generate Christ University focused users
    print("Generating Christ University users...")
    user_count = 50  # Increased from 25 to 50 for more diverse data
    users = []
    for _ in range(user_count):
        user = generate_christ_user_sample()
        users.append(user)
    
    # Insert users
    result = db.users.insert_many(users)
    print(f"Created {len(result.inserted_ids)} user documents")
    
    # Step 2: Generate widgets for users
    print("Generating widgets...")
    widgets = []
    for user in users:
        # Generate 2-5 widgets per user
        widget_count = random.randint(2, 5)
        for _ in range(widget_count):
            widget = generate_widget_sample(user['_id'])
            widgets.append(widget)
    
    # Insert widgets
    if widgets:
        result = db.widgets.insert_many(widgets)
        print(f"Created {len(result.inserted_ids)} widget documents")
    
    # Step 3: Generate bounties and responses
    print("Generating knowledge bounties...")
    bounties = []
    bounty_responses = []
    bounty_votes = []
    
    for user in users:
        # Some users create bounties (50% chance - increased from 40%)
        if random.random() < 0.5:
            # Create 1-4 bounties per creator (increased from 1-3)
            bounty_count = random.randint(1, 4)
            for _ in range(bounty_count):
                # Use user's department for more relevant bounties
                bounty = generate_christ_bounty_sample(user['_id'], user.get('department'))
                bounties.append(bounty)
    
    # Insert bounties
    if bounties:
        result = db.bounties.insert_many(bounties)
        print(f"Created {len(result.inserted_ids)} bounty documents")
    
        # Generate responses for each bounty
        for bounty in bounties:
            # Generate 1-6 responses per bounty (increased from 0-5)
            response_count = random.randint(1, 6)
            for _ in range(response_count):
                # Select a random user as responder (not the creator)
                eligible_users = [u for u in users if str(u['_id']) != str(bounty['creator_id'])]
                if eligible_users:
                    responder = random.choice(eligible_users)
                    response = generate_detailed_bounty_response_sample(bounty['_id'], responder['_id'], False, bounty)
                    bounty_responses.append(response)
            
            # Ensure creator also responds to some bounties (30% chance - increased from 20%)
            if random.random() < 0.3:
                creator_response = generate_detailed_bounty_response_sample(bounty['_id'], bounty['creator_id'], True, bounty)
                bounty_responses.append(creator_response)
    
    # Insert bounty responses
    if bounty_responses:
        result = db.bounty_responses.insert_many(bounty_responses)
        print(f"Created {len(result.inserted_ids)} bounty response documents")
        
        # Generate votes for responses
        for response in bounty_responses:
            # Generate 1-7 votes per response (increased from 0-5)
            vote_count = random.randint(1, 7)
            for _ in range(vote_count):
                # Select a random user as voter (not the responder)
                eligible_users = [u for u in users if str(u['_id']) != str(response['responder_id'])]
                if eligible_users:
                    voter = random.choice(eligible_users)
                    vote = generate_bounty_vote_sample(response['_id'], voter['_id'])
                    bounty_votes.append(vote)
    
    # Insert bounty votes
    if bounty_votes:
        result = db.bounty_votes.insert_many(bounty_votes)
        print(f"Created {len(result.inserted_ids)} bounty vote documents")
    
    # Step 4: Generate marketplace listings and transactions
    print("Generating marketplace listings...")
    listings = []
    transactions = []
    
    for user in users:
        # Some users create listings (40% chance - increased from 30%)
        if random.random() < 0.4:
            # Create 1-4 listings per seller (increased from 1-3)
            listing_count = random.randint(1, 4)
            for _ in range(listing_count):
                # Use user's department for more relevant listings
                listing = generate_marketplace_listing_sample(user['_id'], user.get('department'))
                listings.append(listing)
    
    # Insert listings
    if listings:
        result = db.marketplace_listings.insert_many(listings)
        print(f"Created {len(result.inserted_ids)} marketplace listing documents")
        
        # Generate transactions for listings
        for listing in listings:
            # Generate 0-4 purchases per listing (increased from 0-3)
            purchase_count = random.randint(0, 4)
            for _ in range(purchase_count):
                # Select a random user as buyer (not the seller)
                eligible_users = [u for u in users if str(u['_id']) != str(listing['seller_id'])]
                if eligible_users:
                    buyer = random.choice(eligible_users)
                    transaction = generate_marketplace_transaction_sample(listing['_id'], listing, buyer['_id'])
                    transactions.append(transaction)
    
    # Insert transactions
    if transactions:
        result = db.marketplace_transactions.insert_many(transactions)
        print(f"Created {len(result.inserted_ids)} marketplace transaction documents")
    
    # Step 5: Generate subreddits, threads, and comments
    print("Generating subreddits and threads...")
    subreddits = []
    threads = []
    comments = []
    
    # Create 8-12 subreddits (increased from 5-10)
    subreddit_count = random.randint(8, 12)
    for _ in range(subreddit_count):
        subreddit = generate_subreddit_sample()
        # Assign a random user as creator
        creator = random.choice(users)
        subreddit['creator_id'] = str(creator['_id'])
        subreddits.append(subreddit)
    
    # Insert subreddits
    if subreddits:
        result = db.subreddits.insert_many(subreddits)
        print(f"Created {len(result.inserted_ids)} subreddit documents")
        
        # Generate threads for each subreddit
        for subreddit in subreddits:
            # Generate 4-10 threads per subreddit (increased from 3-8)
            thread_count = random.randint(4, 10)
            for _ in range(thread_count):
                # Select a random user as thread creator
                creator = random.choice(users)
                thread = generate_thread_sample(subreddit['_id'], creator['_id'], subreddit['name'])
                threads.append(thread)
    
    # Insert threads
    if threads:
        result = db.threads.insert_many(threads)
        print(f"Created {len(result.inserted_ids)} thread documents")
        
        # Generate comments for each thread
        for thread in threads:
            # Generate 1-12 comments per thread (increased from 0-10)
            comment_count = random.randint(1, 12)
            thread_comments = []
            
            for _ in range(comment_count):
                # Select a random user as commenter
                commenter = random.choice(users)
                comment = generate_comment_sample(thread['_id'], commenter['_id'], None, thread.get('title'))
                thread_comments.append(comment)
                comments.append(comment)
            
            # Add some nested comments (replies)
            for parent_comment in thread_comments:
                # 40% chance of having replies (increased from 30%)
                if random.random() < 0.4:
                    # Generate 1-4 replies (increased from 1-3)
                    reply_count = random.randint(1, 4)
                    for _ in range(reply_count):
                        # Select a random user as replier
                        replier = random.choice(users)
                        reply = generate_comment_sample(thread['_id'], replier['_id'], parent_comment['_id'], thread.get('title'))
                        comments.append(reply)
    
    # Insert comments
    if comments:
        result = db.comments.insert_many(comments)
        print(f"Created {len(result.inserted_ids)} comment documents")
    
    # Step 6: Generate study spots, occupancy reports, and check-ins
    print("Generating study spots...")
    study_spots = []
    occupancy_reports = []
    check_ins = []
    
    # Create 10-20 study spots (increased from 8-15)
    spot_count = random.randint(10, 20)
    for _ in range(spot_count):
        # Assign a random user as creator
        creator = random.choice(users)
        spot = generate_study_spot_sample(creator['_id'])
        study_spots.append(spot)
    
    # Insert study spots
    if study_spots:
        result = db.study_spots.insert_many(study_spots)
        print(f"Created {len(result.inserted_ids)} study spot documents")
        
        # Generate occupancy reports for spots
        for spot in study_spots:
            # Generate 4-12 occupancy reports per spot (increased from 3-10)
            report_count = random.randint(4, 12)
            for _ in range(report_count):
                # Select a random user as reporter
                reporter = random.choice(users)
                report = generate_occupancy_report_sample(spot['_id'], reporter['_id'])
                occupancy_reports.append(report)
            
            # Generate check-ins for spots
            # Generate 6-18 check-ins per spot (increased from 5-15)
            checkin_count = random.randint(6, 18)
            for _ in range(checkin_count):
                # Select a random user for check-in
                user = random.choice(users)
                check_in = generate_check_in_sample(spot['_id'], user['_id'])
                check_ins.append(check_in)
    
    # Insert occupancy reports
    if occupancy_reports:
        result = db.occupancy_reports.insert_many(occupancy_reports)
        print(f"Created {len(result.inserted_ids)} occupancy report documents")
    
    # Insert check-ins
    if check_ins:
        result = db.check_ins.insert_many(check_ins)
        print(f"Created {len(result.inserted_ids)} check-in documents")
    
    # Step 7: Generate tutor profiles, sessions, and reviews
    print("Generating tutor profiles...")
    tutor_profiles = []
    tutoring_sessions = []
    tutor_reviews = []
    
    for user in users:
        # Some users become tutors (30% chance - increased from 25%)
        if random.random() < 0.3:
            tutor_profile = generate_tutor_profile_sample(user['_id'], user)
            tutor_profiles.append(tutor_profile)
    
    # Insert tutor profiles
    if tutor_profiles:
        result = db.tutor_profiles.insert_many(tutor_profiles)
        print(f"Created {len(result.inserted_ids)} tutor profile documents")
        
        # Generate tutoring sessions
        for profile in tutor_profiles:
            tutor_id = profile['user_id']
            
            # Generate 1-6 sessions per tutor (increased from 0-5)
            session_count = random.randint(1, 6)
            for _ in range(session_count):
                # Select a random user as student (not the tutor)
                eligible_users = [u for u in users if str(u['_id']) != tutor_id]
                if eligible_users:
                    student = random.choice(eligible_users)
                    session = generate_tutoring_session_sample(tutor_id, student['_id'], profile)
                    tutoring_sessions.append(session)
    
    # Insert tutoring sessions
    if tutoring_sessions:
        result = db.tutoring_sessions.insert_many(tutoring_sessions)
        print(f"Created {len(result.inserted_ids)} tutoring session documents")
        
        # Generate reviews for completed sessions
        for session in tutoring_sessions:
            if session['status'] == 'completed':
                review = generate_tutor_review_sample(session['_id'], session)
                if review:
                    tutor_reviews.append(review)
    
    # Insert tutor reviews
    if tutor_reviews:
        result = db.tutor_reviews.insert_many(tutor_reviews)
        print(f"Created {len(result.inserted_ids)} tutor review documents")
    
    # Step 8: Generate coin transactions
    print("Generating coin transactions...")
    coin_transactions = []
    
    # Generate transactions for bounties
    for bounty in bounties:
        # Transaction for posting a bounty (negative amount)
        posting_transaction = generate_coin_transaction_sample(
            bounty['creator_id'], 
            -bounty['reward'], 
            'bounty_posting',
            bounty['_id']
        )
        coin_transactions.append(posting_transaction)
        
        # Find any pinned response for this bounty
        pinned_responses = [r for r in bounty_responses if r['bounty_id'] == bounty['_id'] and r['is_pinned']]
        for response in pinned_responses:
            # Transaction for receiving bounty reward (positive amount)
            reward_transaction = generate_coin_transaction_sample(
                response['responder_id'],
                bounty['reward'],
                'bounty_reward',
                response['_id']
            )
            coin_transactions.append(reward_transaction)
    
    # Generate transactions for marketplace
    for transaction in transactions:
        # Transaction for seller (income)
        seller_transaction = generate_coin_transaction_sample(
            transaction['seller_id'],
            transaction['price'],
            'marketplace_sale',
            transaction['_id']
        )
        coin_transactions.append(seller_transaction)
        
        # Transaction for buyer (expense)
        buyer_transaction = generate_coin_transaction_sample(
            transaction['buyer_id'],
            -transaction['price'],
            'marketplace_purchase',
            transaction['_id']
        )
        coin_transactions.append(buyer_transaction)
    
    # Generate transactions for tutoring
    for session in tutoring_sessions:
        if session['status'] == 'completed':
            # Transaction for tutor (income)
            tutor_transaction = generate_coin_transaction_sample(
                session['tutor_id'],
                session['payment_amount'],
                'tutoring_income',
                session['_id']
            )
            coin_transactions.append(tutor_transaction)
            
            # Transaction for student (expense)
            student_transaction = generate_coin_transaction_sample(
                session['student_id'],
                -session['payment_amount'],
                'tutoring_payment',
                session['_id']
            )
            coin_transactions.append(student_transaction)
    
    # Generate upvote reward transactions
    # For simplicity, we'll just create some random upvote rewards
    for user in users:
        # 60% chance of receiving upvote rewards (increased from 50%)
        if random.random() < 0.6:
            # Generate 1-6 upvote reward transactions (increased from 1-5)
            upvote_count = random.randint(1, 6)
            for _ in range(upvote_count):
                amount = random.randint(5, 25)  # Increased maximum from 20 to 25
                upvote_transaction = generate_coin_transaction_sample(
                    user['_id'],
                    amount,
                    'upvote_reward'
                )
                coin_transactions.append(upvote_transaction)
    
    # Generate system bonus transactions (welcome bonuses, etc.)
    for user in users:
        # Everyone gets a welcome bonus
        welcome_bonus = generate_coin_transaction_sample(
            user['_id'],
            100,  # Standard welcome bonus
            'system_bonus'
        )
        coin_transactions.append(welcome_bonus)
        
        # 40% chance of additional system bonuses (increased from 30%)
        if random.random() < 0.4:
            # Generate 1-4 additional bonus transactions (increased from 1-3)
            bonus_count = random.randint(1, 4)
            for _ in range(bonus_count):
                amount = random.choice([50, 100, 200, 500, 1000])  # Added 1000 as a possible bonus
                bonus_transaction = generate_coin_transaction_sample(
                    user['_id'],
                    amount,
                    'system_bonus'
                )
                coin_transactions.append(bonus_transaction)
    
    # Insert coin transactions
    if coin_transactions:
        result = db.coin_transactions.insert_many(coin_transactions)
        print(f"Created {len(result.inserted_ids)} coin transaction documents")
    
    # Step 9: Generate conversations and messages
    print("Generating conversations and messages...")
    conversations = []
    messages = []
    
    # Create some one-on-one conversations
    pair_count = min(20, len(users) * (len(users) - 1) // 2)  # Up to 20 pairs (increased from 15)
    for _ in range(pair_count):
        # Select two different random users
        user1, user2 = random.sample(users, 2)
        conversation = generate_conversation_sample([user1['_id'], user2['_id']])
        conversations.append(conversation)
    
    # Create some group conversations (3-5 participants)
    group_count = min(10, len(users) // 3)  # Up to 10 group conversations
    for _ in range(group_count):
        # Select 3-5 random users
        group_size = random.randint(3, 5)
        group_members = random.sample(users, group_size)
        group_ids = [member['_id'] for member in group_members]
        group_conversation = generate_conversation_sample(group_ids)
        conversations.append(group_conversation)
    
    # Insert conversations
    if conversations:
        result = db.conversations.insert_many(conversations)
        print(f"Created {len(result.inserted_ids)} conversation documents")
        
        # Generate messages for each conversation
        for conversation in conversations:
            # Generate 1-15 messages per conversation (increased from 1-10)
            message_count = random.randint(1, 15)
            participants = conversation['participants']
            
            for _ in range(message_count):
                # Select a random participant as sender
                sender_id = ObjectId(random.choice(participants))
                # The other participants are recipients
                recipient_ids = [ObjectId(p) for p in participants if p != str(sender_id)]
                
                message = generate_message_sample(conversation['_id'], sender_id, recipient_ids)
                messages.append(message)
    
    # Insert messages
    if messages:
        result = db.messages.insert_many(messages)
        print(f"Created {len(result.inserted_ids)} message documents")
    
    # Create indexes for better performance
    print("Creating database indexes...")
    
    # User indexes
    db.users.create_index("email", unique=True)
    db.users.create_index("username")
    db.users.create_index("firebase_uid", unique=True)
    db.users.create_index("university")
    db.users.create_index("department")
    
    # Widget indexes
    db.widgets.create_index([("user_id", 1), ("widget_type", 1)])
    
    # Bounty indexes
    db.bounties.create_index("creator_id")
    db.bounties.create_index("category")
    db.bounties.create_index("tags")
    db.bounties.create_index("status")
    db.bounties.create_index([("created_at", -1)])
    
    # Bounty response indexes
    db.bounty_responses.create_index("bounty_id")
    db.bounty_responses.create_index("responder_id")
    db.bounty_responses.create_index([("upvotes", -1)])
    
    # Marketplace indexes
    db.marketplace_listings.create_index("seller_id")
    db.marketplace_listings.create_index("category")
    db.marketplace_listings.create_index("subject")
    db.marketplace_listings.create_index("type")
    db.marketplace_listings.create_index([("created_at", -1)])
    db.marketplace_listings.create_index([("price", 1)])
    
    # Subreddit indexes
    db.subreddits.create_index("name", unique=True)
    db.subreddits.create_index("tags")
    db.subreddits.create_index([("member_count", -1)])
    
    # Thread indexes
    db.threads.create_index("subreddit_id")
    db.threads.create_index("creator_id")
    db.threads.create_index("tags")
    db.threads.create_index([("created_at", -1)])
    db.threads.create_index([("upvotes", -1)])
    
    # Comment indexes
    db.comments.create_index("thread_id")
    db.comments.create_index("parent_id")
    db.comments.create_index("author_id")
    db.comments.create_index([("created_at", -1)])
    
    # Study spot indexes
    db.study_spots.create_index([("location", "2dsphere")])
    db.study_spots.create_index("created_by")
    db.study_spots.create_index([("name", "text"), ("description", "text")])
    
    # Tutor indexes
    db.tutor_profiles.create_index("user_id", unique=True)
    db.tutor_profiles.create_index("subjects")
    db.tutor_profiles.create_index([("hourly_rate", 1)])
    db.tutor_profiles.create_index([("average_rating", -1)])
    
    # Session indexes
    db.tutoring_sessions.create_index("tutor_id")
    db.tutoring_sessions.create_index("student_id")
    db.tutoring_sessions.create_index("scheduled_time")
    db.tutoring_sessions.create_index("status")
    
    # Coin transaction indexes
    db.coin_transactions.create_index("user_id")
    db.coin_transactions.create_index("transaction_type")
    db.coin_transactions.create_index("created_at")
    db.coin_transactions.create_index([("amount", -1)])
    
    # Conversation and message indexes
    db.conversations.create_index("participants")
    db.conversations.create_index([("updated_at", -1)])
    db.messages.create_index("conversation_id")
    db.messages.create_index("sender_id")
    db.messages.create_index([("created_at", -1)])
    db.messages.create_index("read_by")
    
    print("Database setup complete!")

# Main execution block
if __name__ == "__main__":
    setup_database()