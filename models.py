from datetime import datetime, timezone
from typing import Any
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class User(BaseModel):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    headline = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='user', lazy=True, cascade="all, delete-orphan")
    progress_records = db.relationship('Progress', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Course(BaseModel):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)  # Web Development, Programming, Design, AI & Data
    difficulty = db.Column(db.String(20), nullable=False)  # Beginner, Intermediate, Advanced
    duration = db.Column(db.String(30), nullable=False)    # e.g., "12 hours", "8 hours"
    price = db.Column(db.Float, default=0.0)               # 0.0 means Free, or specific price e.g., 49.99
    thumbnail = db.Column(db.String(255), nullable=True)   # SVG or image URL
    gradient_start = db.Column(db.String(7), default='#4f46e5')  # Indigo
    gradient_end = db.Column(db.String(7), default='#7c3aed')    # Violet
    instructor = db.Column(db.String(100), default='Nexora Academy')
    rating = db.Column(db.Float, default=4.8)
    skills = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    lectures = db.relationship('Lecture', backref='course', lazy=True, order_by='Lecture.order_num', cascade="all, delete-orphan")
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade="all, delete-orphan")
    materials = db.relationship('StudyMaterial', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.title}>"


class Lecture(BaseModel):
    __tablename__ = 'lectures'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    duration = db.Column(db.String(20), nullable=False)    # e.g., "10:15", "8:45"
    video_url = db.Column(db.String(255), nullable=False)  # URL to youtube, vimeo, or local file
    description = db.Column(db.Text, nullable=True)
    order_num = db.Column(db.Integer, nullable=False)      # Position inside the course curriculum
    resources = db.Column(db.Text, nullable=True)          # Markdown lists of resources, downloads, or links
    
    # Relationships
    progress_records = db.relationship('Progress', backref='lecture', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='lecture', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lecture {self.title} (Course ID: {self.course_id})>"


class Enrollment(BaseModel):
    __tablename__ = 'enrollments'
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='uq_user_course_enrollment'),)
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(20), default='free') # 'free', 'paid'
    payment_amount = db.Column(db.Float, default=0.0)
    transaction_id = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Enrollment User: {self.user_id} Course: {self.course_id}>"


class Progress(BaseModel):
    __tablename__ = 'progress'
    __table_args__ = (db.UniqueConstraint('user_id', 'lecture_id', name='uq_user_lecture_progress'),)
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Progress User: {self.user_id} Lecture: {self.lecture_id}>"


class StudyMaterial(BaseModel):
    __tablename__ = 'study_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'PDF', 'PPT', 'Source Code', 'Notes', 'Practice Questions'
    file_size = db.Column(db.String(20), nullable=False)  # e.g. "2.4 MB"
    file_url = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    category = db.Column(db.String(50), nullable=False, default='General')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)

    def __repr__(self):
        return f"<StudyMaterial {self.title} ({self.file_type})>"


class Comment(BaseModel):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Comment user={self.user_id} lecture={self.lecture_id}>"


class QuizQuestion(BaseModel):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    question_text = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', 'D'

    # Relationship
    course = db.relationship('Course', backref=db.backref('quiz_questions', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<QuizQuestion id={self.id} course_id={self.course_id}>"


class QuizScore(BaseModel):
    __tablename__ = 'quiz_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', backref=db.backref('quiz_scores', lazy=True, cascade="all, delete-orphan"))
    course = db.relationship('Course', backref=db.backref('quiz_scores', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<QuizScore user={self.user_id} course={self.course_id} score={self.score}/{self.total}>"
