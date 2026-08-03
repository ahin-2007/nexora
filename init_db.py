from flask import Flask
from config import Config
from models import db, Course, Lecture, User, StudyMaterial, QuizQuestion

def init_database():
    """Initialize database with schema and sample data"""
    print("[*] Initializing database...")
    
    db.drop_all()
    db.create_all()
    
    # Add admin user
    admin = User(
        name="Administrator",
        email="admin@nexora.com",
        bio="Platform Admin",
        headline="Senior Instructor",
        phone="+1 (555) 019-2831",
        avatar_url="/static/uploads/admin_avatar.jpg"
    )
    admin.set_password("admin123")
    db.session.add(admin)
    
    # Sample courses
    courses = [
        {
            "title": "Modern Web Development",
            "slug": "web-development",
            "description": "Master HTML5, CSS3, JavaScript, and responsive design.",
            "category": "Web Development",
            "difficulty": "Beginner",
            "duration": "10h 30m",
            "price": 0.0,
            "gradient_start": "#4f46e5",
            "gradient_end": "#7c3aed",
            "instructor": "Sarah Jenkins",
            "rating": 4.9,
            "skills": "HTML5, CSS3, JavaScript, Responsive Design",
            "requirements": "Basic computer knowledge"
        },
        {
            "title": "Python Programming Masterclass",
            "slug": "python-programming",
            "description": "Learn Python 3 from basics to advanced OOP.",
            "category": "Programming",
            "difficulty": "Beginner",
            "duration": "8h 45m",
            "price": 0.0,
            "gradient_start": "#3b82f6",
            "gradient_end": "#06b6d4",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.95,
            "skills": "Python, OOP, Data Structures",
            "requirements": "No prior experience needed"
        },
        {
            "title": "ReactJS Component Architecture",
            "slug": "reactjs-mastery",
            "description": "Build modern UIs with React Hooks and state management.",
            "category": "Web Development",
            "difficulty": "Intermediate",
            "duration": "11h 10m",
            "price": 2499.0,
            "gradient_start": "#06b6d4",
            "gradient_end": "#3b82f6",
            "instructor": "Emma Thompson",
            "rating": 4.87,
            "skills": "React, Hooks, State Management",
            "requirements": "JavaScript knowledge"
        },
        {
            "title": "SQL & Relational Databases",
            "slug": "sql-database",
            "description": "Master SQL and database design patterns.",
            "category": "AI & Data",
            "difficulty": "Intermediate",
            "duration": "6h 50m",
            "price": 0.0,
            "gradient_start": "#10b981",
            "gradient_end": "#059669",
            "instructor": "John Smith",
            "rating": 4.8,
            "skills": "SQL, Database Design",
            "requirements": "Basic database concepts"
        },
        {
            "title": "Introduction to UI/UX Design",
            "slug": "ui-ux-design",
            "description": "Learn visual design principles, wireframing, and user research using Figma.",
            "category": "Design",
            "difficulty": "Beginner",
            "duration": "9h 15m",
            "price": 0.0,
            "gradient_start": "#f59e0b",
            "gradient_end": "#d97706",
            "instructor": "David Kim",
            "rating": 4.85,
            "skills": "Figma, Wireframing, User Research, Prototyping",
            "requirements": "No prior design experience required"
        },
        {
            "title": "Machine Learning & AI Bootcamp",
            "slug": "machine-learning",
            "description": "Build predictive models with Python, Scikit-Learn, and TensorFlow.",
            "category": "AI & Data",
            "difficulty": "Advanced",
            "duration": "18h 30m",
            "price": 4999.0,
            "gradient_start": "#8b5cf6",
            "gradient_end": "#ec4899",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.97,
            "skills": "Supervised Learning, Unsupervised Learning, Neural Networks",
            "requirements": "Python Programming knowledge, Basic Linear Algebra"
        },
        {
            "title": "Advanced JavaScript & ES6+",
            "slug": "advanced-js",
            "description": "Deep dive into closures, async programming, Promises, and JavaScript engine internals.",
            "category": "Programming",
            "difficulty": "Intermediate",
            "duration": "8h 12m",
            "price": 999.0,
            "gradient_start": "#facc15",
            "gradient_end": "#eab308",
            "instructor": "Sarah Jenkins",
            "rating": 4.92,
            "skills": "Async/Await, Promises, Closures, Prototypes, ES6+",
            "requirements": "Basic JavaScript knowledge"
        },
        {
            "title": "Mastering Figma for Web Design",
            "slug": "mastering-figma",
            "description": "Master components, auto-layout, interactive prototypes, and design systems.",
            "category": "Design",
            "difficulty": "Intermediate",
            "duration": "7h 45m",
            "price": 1499.0,
            "gradient_start": "#ec4899",
            "gradient_end": "#f43f5e",
            "instructor": "David Kim",
            "rating": 4.79,
            "skills": "Figma Components, Auto Layout, Prototyping, Design Systems",
            "requirements": "Basic design concepts"
        },
        {
            "title": "Full-Stack Web Apps with Node & Express",
            "slug": "nodejs-express",
            "description": "Develop and deploy robust, secure, and fast backend applications and REST APIs.",
            "category": "Web Development",
            "difficulty": "Advanced",
            "duration": "14h 20m",
            "price": 2999.0,
            "gradient_start": "#10b981",
            "gradient_end": "#3b82f6",
            "instructor": "Emma Thompson",
            "rating": 4.91,
            "skills": "Node.js, Express, MongoDB, REST APIs, JWT Auth",
            "requirements": "JavaScript, Basic Web Dev"
        },
        {
            "title": "C++ Programming for Beginners",
            "slug": "cpp-beginners",
            "description": "Master C++ syntax, memory management, pointers, and object-oriented programming.",
            "category": "Programming",
            "difficulty": "Beginner",
            "duration": "12h 05m",
            "price": 0.0,
            "gradient_start": "#6366f1",
            "gradient_end": "#4338ca",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.88,
            "skills": "C++ Syntax, Pointers, Memory Management, OOP",
            "requirements": "No coding background required"
        },
        {
            "title": "Product Design & Prototyping",
            "slug": "product-design",
            "description": "Learn to translate user requirements into interactive prototypes and user-centric flows.",
            "category": "Design",
            "difficulty": "Advanced",
            "duration": "15h 10m",
            "price": 3499.0,
            "gradient_start": "#f43f5e",
            "gradient_end": "#be123c",
            "instructor": "David Kim",
            "rating": 4.86,
            "skills": "User Flow, Prototyping, Usability Testing, Interactive Design",
            "requirements": "Figma basics"
        },
        {
            "title": "Data Visualization with Tableau",
            "slug": "tableau-viz",
            "description": "Create charts, dashboards, and storytelling views using Tableau Public.",
            "category": "AI & Data",
            "difficulty": "Beginner",
            "duration": "7h 25m",
            "price": 1999.0,
            "gradient_start": "#0284c7",
            "gradient_end": "#0369a1",
            "instructor": "John Smith",
            "rating": 4.82,
            "skills": "Tableau Dashboards, Data Blending, Storytelling, Visual Design",
            "requirements": "Basic analytical thinking"
        },
        {
            "title": "Next.js Production-Ready Architectures",
            "slug": "nextjs-architecture",
            "description": "Master Next.js App Router, SSR, SSG, Server Actions, and authentication.",
            "category": "Web Development",
            "difficulty": "Advanced",
            "duration": "13h 40m",
            "price": 3999.0,
            "gradient_start": "#18181b",
            "gradient_end": "#27272a",
            "instructor": "Emma Thompson",
            "rating": 4.94,
            "skills": "Next.js, SSR, Server Actions, App Router, Performance Tuning",
            "requirements": "React & JS intermediate knowledge"
        },
        {
            "title": "Rust Systems Programming",
            "slug": "rust-systems",
            "description": "Understand ownership, borrowing, lifetimes, safety, and performance with Rust.",
            "category": "Programming",
            "difficulty": "Advanced",
            "duration": "16h 15m",
            "price": 4499.0,
            "gradient_start": "#ea580c",
            "gradient_end": "#c2410c",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.96,
            "skills": "Rust, Memory Safety, Concurrency, Cargo Ecosystem",
            "requirements": "C or C++ basic understanding is recommended"
        },
        {
            "title": "Introduction to Mobile App Design",
            "slug": "mobile-design",
            "description": "Understand iOS and Android platform design guidelines, human interfaces, and layout structures.",
            "category": "Design",
            "difficulty": "Beginner",
            "duration": "5h 50m",
            "price": 0.0,
            "gradient_start": "#d946ef",
            "gradient_end": "#a21caf",
            "instructor": "David Kim",
            "rating": 4.75,
            "skills": "iOS HIG, Android Material Design, Mobile Wireframing",
            "requirements": "No prerequisite tools required"
        },
        {
            "title": "Deep Learning & Computer Vision",
            "slug": "deep-learning",
            "description": "Master CNNs, RNNs, transfer learning, and image classification with PyTorch.",
            "category": "AI & Data",
            "difficulty": "Advanced",
            "duration": "20h 10m",
            "price": 5999.0,
            "gradient_start": "#e11d48",
            "gradient_end": "#4c1d95",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.98,
            "skills": "PyTorch, Neural Networks, Computer Vision, CNNs",
            "requirements": "Python, basic Machine Learning concepts"
        },
        {
            "title": "Tailwind CSS Responsive Design",
            "slug": "tailwind-responsive",
            "description": "Build modern layouts, responsive sites, and reusable templates rapidly with Tailwind.",
            "category": "Web Development",
            "difficulty": "Beginner",
            "duration": "4h 30m",
            "price": 499.0,
            "gradient_start": "#06b6d4",
            "gradient_end": "#0891b2",
            "instructor": "Sarah Jenkins",
            "rating": 4.89,
            "skills": "Tailwind CSS, Responsive Design, Flexbox, CSS Grid",
            "requirements": "HTML & CSS basics"
        },
        {
            "title": "Java Fundamentals & OOP",
            "slug": "java-oop",
            "description": "Learn Java syntax, OOP design patterns, inheritance, polymorphism, and collections.",
            "category": "Programming",
            "difficulty": "Beginner",
            "duration": "10h 15m",
            "price": 0.0,
            "gradient_start": "#0284c7",
            "gradient_end": "#4f46e5",
            "instructor": "Dr. Alex Rivera",
            "rating": 4.83,
            "skills": "Java, OOP, Design Patterns, Exception Handling",
            "requirements": "Basic programming curiosity"
        },
        {
            "title": "Typography & Color Theory",
            "slug": "typography-color",
            "description": "Study type pairing, hierarchy, color psychology, and how to create clean, readable interfaces.",
            "category": "Design",
            "difficulty": "Intermediate",
            "duration": "6h 20m",
            "price": 799.0,
            "gradient_start": "#fb7185",
            "gradient_end": "#e11d48",
            "instructor": "David Kim",
            "rating": 4.81,
            "skills": "Typography, Color Psychology, Visual Hierarchy, Web Safe Fonts",
            "requirements": "Basic interface design"
        },
        {
            "title": "Prompt Engineering for AI",
            "slug": "prompt-engineering",
            "description": "Learn to query LLMs effectively, build custom system prompts, and use advanced prompting techniques.",
            "category": "AI & Data",
            "difficulty": "Beginner",
            "duration": "5h 15m",
            "price": 1299.0,
            "gradient_start": "#0d9488",
            "gradient_end": "#0f766e",
            "instructor": "John Smith",
            "rating": 4.9,
            "skills": "System Prompts, Few-shot prompting, LLMs, AI integrations",
            "requirements": "Basic computer usage"
        },
        {
            "title": "Web Security & Ethical Hacking",
            "slug": "web-security",
            "description": "Understand OWASP Top 10, cross-site scripting (XSS), SQL injection, and web app defense.",
            "category": "Web Development",
            "difficulty": "Intermediate",
            "duration": "12h 40m",
            "price": 3299.0,
            "gradient_start": "#dc2626",
            "gradient_end": "#991b1b",
            "instructor": "Sarah Jenkins",
            "rating": 4.93,
            "skills": "OWASP Top 10, Penetration Testing, Web Security, HTTPS",
            "requirements": "HTML, JS, and basic web protocols"
        }
    ]
    
    # Add courses with lectures
    for course_data in courses:
        course = Course(
            title=course_data["title"],
            slug=course_data["slug"],
            description=course_data["description"],
            category=course_data["category"],
            difficulty=course_data["difficulty"],
            duration=course_data["duration"],
            price=course_data["price"],
            gradient_start=course_data["gradient_start"],
            gradient_end=course_data["gradient_end"],
            instructor=course_data["instructor"],
            rating=course_data["rating"],
            skills=course_data["skills"],
            requirements=course_data["requirements"]
        )
        db.session.add(course)
        db.session.flush()
        
        # Add sample lecture
        lecture = Lecture(
            course_id=course.id,
            title=f"Introduction to {course_data['title']}",
            duration="15:30",
            video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
            description=f"Get started with {course_data['title']}",
            order_num=1,
            resources="https://example.com/resources"
        )
        db.session.add(lecture)
        
        # Add sample quiz
        quiz = QuizQuestion(
            course_id=course.id,
            question_text="What is the first step to learning this course?",
            option_a="Start coding immediately",
            option_b="Watch all the videos",
            option_c="Read the documentation",
            option_d="Practice on exercises",
            correct_option="C"
        )
        db.session.add(quiz)
    
    # Add study materials
    materials = [
        {
            "title": "Web Development Cheat Sheet",
            "file_type": "PDF",
            "file_size": "2.4 MB",
            "file_url": "/static/materials/web_dev.pdf",
            "category": "Web Development"
        },
        {
            "title": "Python Syntax Guide",
            "file_type": "PDF",
            "file_size": "1.8 MB",
            "file_url": "/static/materials/python.pdf",
            "category": "Programming"
        },
        {
            "title": "React Component Lifecycle & Hooks Cheat Sheet",
            "file_type": "PDF",
            "file_size": "2.1 MB",
            "file_url": "/static/materials/react_hooks.pdf",
            "category": "Web Development"
        },
        {
            "title": "SQL Cheat Sheet & Joins Diagram",
            "file_type": "PDF",
            "file_size": "1.5 MB",
            "file_url": "/static/materials/sql_queries.pdf",
            "category": "AI & Data"
        },
        {
            "title": "Machine Learning Algorithms Map",
            "file_type": "PDF",
            "file_size": "3.4 MB",
            "file_url": "/static/materials/ml_algorithms.pdf",
            "category": "AI & Data"
        },
        {
            "title": "Figma Web Design Shortcuts",
            "file_type": "PDF",
            "file_size": "1.2 MB",
            "file_url": "/static/materials/figma_shortcuts.pdf",
            "category": "Design"
        },
        {
            "title": "Git & GitHub Command Reference",
            "file_type": "PDF",
            "file_size": "850 KB",
            "file_url": "/static/materials/git_reference.pdf",
            "category": "Programming"
        },
        {
            "title": "Node.js REST API Boilerplate",
            "file_type": "Source Code",
            "file_size": "150 KB",
            "file_url": "/static/materials/node_boilerplate.zip",
            "category": "Web Development"
        },
        {
            "title": "Java Object-Oriented Design Patterns",
            "file_type": "PPT",
            "file_size": "4.2 MB",
            "file_url": "/static/materials/java_oop_patterns.ppt",
            "category": "Programming"
        }
    ]
    
    for mat in materials:
        study_mat = StudyMaterial(
            title=mat["title"],
            file_type=mat["file_type"],
            file_size=mat["file_size"],
            file_url=mat["file_url"],
            category=mat["category"]
        )
        db.session.add(study_mat)
    
    db.session.commit()
    print("[SUCCESS] Database initialized successfully!")

if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        init_database()
