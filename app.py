import os
import uuid
from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
from config import Config
from models import db, User, Course, Lecture, Enrollment, Progress, StudyMaterial, QuizQuestion
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'videos')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def normalize_video_url(video_url: str) -> str:
    if not video_url:
        return ''

    video_url = video_url.strip()
    parsed = urlparse(video_url)
    netloc = parsed.netloc.lower()
    path = parsed.path or ''

    if 'youtu.be' in netloc:
        video_id = path.lstrip('/')
        query = parse_qs(parsed.query)
        params = {}
        if 'list' in query:
            params['list'] = query['list'][0]
        if video_id:
            embed_url = f'https://www.youtube.com/embed/{video_id}'
            if params:
                embed_url += '?' + urlencode(params)
            return embed_url

    if 'youtube.com' in netloc:
        if '/watch' in path:
            query = parse_qs(parsed.query)
            video_id = query.get('v', [None])[0]
            params = {}
            if 'list' in query:
                params['list'] = query['list'][0]
            if video_id:
                embed_url = f'https://www.youtube.com/embed/{video_id}'
                if params:
                    embed_url += '?' + urlencode(params)
                return embed_url
        if '/shorts/' in path:
            video_id = path.split('/shorts/')[-1].strip('/')
            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'
        if '/embed/' in path:
            return video_url

    return video_url


def save_uploaded_video(video_file):
    if not video_file or not getattr(video_file, 'filename', None):
        return None

    filename = secure_filename(video_file.filename)
    if not filename:
        return None

    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = {'.mp4', '.webm', '.mov', '.mkv', '.avi', '.ogg'}
    if ext not in allowed_extensions:
        raise ValueError('Only video files such as MP4, WebM, MOV, MKV, AVI, or OGG are supported.')

    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    video_file.save(save_path)
    return f"/static/uploads/videos/{unique_name}"

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            existing_cols = {col['name'] for col in inspector.get_columns('users')}
            required_cols = {
                'bio': 'TEXT',
                'phone': 'VARCHAR(20)',
                'headline': 'VARCHAR(100)',
                'avatar_url': 'VARCHAR(255)'
            }
            with db.engine.connect() as conn:
                for col_name, col_type in required_cols.items():
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        print(f"[!] Schema check warning: {e}")


# Inject logged-in user into template context
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        # Load user from DB. If not found (e.g. deleted), clear session.
        g.user = db.session.get(User, user_id)
        if g.user is None:
            session.clear()

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please register or log in to access this feature.', 'warning')
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def home():
    # Fetch 3 featured courses for the homepage
    courses = Course.query.limit(3).all()
    
    # Calculate some mock statistics
    stats = {
        'students_count': '15,400+',
        'courses_count': '9+',
        'instructors_count': '12',
        'rating': '4.9/5.0'
    }
    
    # Check what courses the user is enrolled in to display contextually
    enrolled_course_ids = []
    if g.user:
        enrolled_course_ids = [e.course_id for e in g.user.enrollments]
        
    return render_template('home.html', courses=courses, stats=stats, enrolled_course_ids=enrolled_course_ids)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
def courses():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', 'All').strip()
    
    query = Course.query
    
    # Apply search filter
    if search_query:
        query = query.filter((Course.title.like(f'%{search_query}%')) | (Course.description.like(f'%{search_query}%')))
        
    # Apply category filter
    if category_filter and category_filter != 'All':
        query = query.filter_by(category=category_filter)
        
    all_courses = query.all()
    
    # Track student progress for each course
    progress_map = {}
    enrolled_course_ids = []
    
    if g.user:
        enrolled_course_ids = [e.course_id for e in g.user.enrollments]
        
        # Calculate completion percent for enrolled courses
        for course in all_courses:
            if course.id in enrolled_course_ids:
                total_lectures = len(course.lectures)
                if total_lectures == 0:
                    progress_map[course.id] = 0
                    continue
                
                # Count completed lectures for this user
                lecture_ids = [l.id for l in course.lectures]
                completed_count = Progress.query.filter(
                    Progress.user_id == g.user.id,
                    Progress.lecture_id.in_(lecture_ids)
                ).count()
                
                progress_map[course.id] = int((completed_count / total_lectures) * 100)
    
    # Get distinct categories for filtering layout
    db_categories = [row[0] for row in db.session.query(Course.category).distinct().order_by(Course.category).all()]
    categories = ['All'] + [c for c in db_categories if c]
    
    return render_template(
        'courses.html',
        courses=all_courses,
        categories=categories,
        selected_category=category_filter,
        search_query=search_query,
        enrolled_course_ids=enrolled_course_ids,
        progress_map=progress_map
    )

@app.route('/course/<slug>')
def course_details(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Check user enrollment status
    is_enrolled = False
    progress_percent = 0
    if g.user:
        enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course.id).first()
        is_enrolled = enrollment is not None
        
        if is_enrolled:
            total_lectures = len(course.lectures)
            if total_lectures > 0:
                lecture_ids = [l.id for l in course.lectures]
                completed_count = Progress.query.filter(
                    Progress.user_id == g.user.id,
                    Progress.lecture_id.in_(lecture_ids)
                ).count()
                progress_percent = int((completed_count / total_lectures) * 100)
                
    return render_template('course_details.html', course=course, is_enrolled=is_enrolled, progress_percent=progress_percent)

@app.route('/course/<slug>/enroll', methods=['POST'])
@login_required
def enroll(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Prevent duplicate enrollment
    existing_enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course.id).first()
    if not existing_enrollment:
        if course.price > 0:
            return redirect(url_for('payment', slug=course.slug))
            
        new_enrollment = Enrollment(
            user_id=g.user.id, 
            course_id=course.id, 
            payment_status='free', 
            payment_amount=0.0
        )
        db.session.add(new_enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in {course.title}!', 'success')
    
    # Redirect to the first lecture of the course
    first_lecture = Lecture.query.filter_by(course_id=course.id).order_by(Lecture.order_num).first()
    if first_lecture:
        return redirect(url_for('learn', slug=course.slug, lecture_id=first_lecture.id))
    
    return redirect(url_for('course_details', slug=course.slug))

@app.route('/course/<slug>/payment', methods=['GET', 'POST'])
@login_required
def payment(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course.id).first()
    if existing_enrollment:
        flash('You are already enrolled in this course!', 'info')
        return redirect(url_for('course_details', slug=course.slug))
        
    if request.method == 'POST':
        # Generate mock transaction ID
        import uuid
        tx_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Create enrollment
        new_enrollment = Enrollment(
            user_id=g.user.id,
            course_id=course.id,
            payment_status='paid',
            payment_amount=course.price,
            transaction_id=tx_id
        )
        db.session.add(new_enrollment)
        db.session.commit()
        
        flash(f'Payment successful! Welcome to {course.title}.', 'success')
        
        # Redirect to the first lecture of the course
        first_lecture = Lecture.query.filter_by(course_id=course.id).order_by(Lecture.order_num).first()
        if first_lecture:
            return redirect(url_for('learn', slug=course.slug, lecture_id=first_lecture.id))
        return redirect(url_for('course_details', slug=course.slug))
        
    return render_template('payment.html', course=course)

@app.route('/course/<slug>/learn')
@login_required
def learn_intro(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Verify enrollment
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course.id).first()
    if not enrollment:
        flash('You must enroll in this course first.', 'warning')
        return redirect(url_for('course_details', slug=course.slug))
        
    # Redirect to first lecture or last watched lecture
    first_lecture = Lecture.query.filter_by(course_id=course.id).order_by(Lecture.order_num).first()
    if first_lecture:
        return redirect(url_for('learn', slug=course.slug, lecture_id=first_lecture.id))
        
    flash('This course has no lectures added yet.', 'info')
    return redirect(url_for('course_details', slug=course.slug))

@app.route('/course/<slug>/learn/<int:lecture_id>')
@login_required
def learn(slug, lecture_id):
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Verify enrollment
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course.id).first()
    if not enrollment:
        flash('You must enroll in this course to start learning.', 'warning')
        return redirect(url_for('course_details', slug=course.slug))
        
    lecture = Lecture.query.filter_by(id=lecture_id, course_id=course.id).first_or_404()
    lecture_video_url = normalize_video_url(lecture.video_url)
    
    # Fetch all lectures for playlist navigation
    all_lectures = Lecture.query.filter_by(course_id=course.id).order_by(Lecture.order_num).all()
    
    # Find active lecture indexing for next/prev buttons
    curr_index = next((i for i, l in enumerate(all_lectures) if l.id == lecture.id), 0)
    prev_lecture = all_lectures[curr_index - 1] if curr_index > 0 else None
    next_lecture = all_lectures[curr_index + 1] if curr_index < len(all_lectures) - 1 else None
    
    # Fetch completed lecture IDs for completion styling
    completed_lecture_ids = [
        p.lecture_id for p in Progress.query.filter_by(user_id=g.user.id).all()
    ]
    
    # Is the current lecture completed?
    is_completed = lecture.id in completed_lecture_ids
    
    # Count course progression percentage
    total_lectures = len(all_lectures)
    progress_percent = 0
    if total_lectures > 0:
        completed_count = sum(1 for l in all_lectures if l.id in completed_lecture_ids)
        progress_percent = int((completed_count / total_lectures) * 100)

    return render_template(
        'video.html',
        course=course,
        lecture=lecture,
        lecture_video_url=lecture_video_url,
        lectures=all_lectures,
        completed_lecture_ids=completed_lecture_ids,
        is_completed=is_completed,
        prev_lecture=prev_lecture,
        next_lecture=next_lecture,
        progress_percent=progress_percent
    )

@app.route('/api/progress/toggle', methods=['POST'])
@login_required
def toggle_progress():
    data = request.get_json() or {}
    lecture_id = data.get('lecture_id')
    
    if not lecture_id:
        return jsonify({'error': 'Missing lecture_id'}), 400
        
    lecture = db.session.get(Lecture, lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404
        
    # Verify enrollment
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=lecture.course_id).first()
    if not enrollment:
        return jsonify({'error': 'Unauthorized. Not enrolled in course.'}), 403
        
    existing_progress = Progress.query.filter_by(user_id=g.user.id, lecture_id=lecture_id).first()
    
    completed = False
    if existing_progress:
        # Toggle: Remove complete status
        db.session.delete(existing_progress)
        completed = False
    else:
        # Toggle: Add complete status
        new_progress = Progress(user_id=g.user.id, lecture_id=lecture_id)
        db.session.add(new_progress)
        completed = True
        
    db.session.commit()
    
    # Calculate updated course statistics
    course_lectures = Lecture.query.filter_by(course_id=lecture.course_id).all()
    total_lectures = len(course_lectures)
    
    completed_count = Progress.query.filter(
        Progress.user_id == g.user.id,
        Progress.lecture_id.in_([l.id for l in course_lectures])
    ).count()
    
    progress_percent = int((completed_count / total_lectures) * 100) if total_lectures > 0 else 0
    
    # Update enrollment completed status if done
    if progress_percent == 100 and not enrollment.completed:
        enrollment.completed = True
        enrollment.completed_at = datetime.now(timezone.utc)
        db.session.commit()
    elif progress_percent < 100 and enrollment.completed:
        enrollment.completed = False
        enrollment.completed_at = None
        db.session.commit()
        
    return jsonify({
        'completed': completed,
        'progress_percent': progress_percent,
        'completed_count': completed_count,
        'total_count': total_lectures
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not name or not email or not password:
            flash('Please fill in all registration fields.', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists.', 'danger')
            return render_template('register.html')
            
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log user in instantly
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['user_email'] = new_user.email
        
        flash('Account successfully registered! Welcome to Nexora.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))
        
    next_url = request.args.get('next', '')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in all credentials fields.', 'danger')
            return render_template('login.html', next=next_url)
            
        if email == 'admin@nexora.com':
            flash('Admin accounts must sign in via the Admin Login portal.', 'warning')
            return redirect(url_for('admin_login', next=next_url))
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', next=next_url)
            
        # Success log
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        
        flash(f'Welcome back, {user.name}!', 'success')
        
        # Guard check redirect urls against open redirects
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard'))
        
    return render_template('login.html', next=next_url)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have successfully logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    enrollments = Enrollment.query.filter_by(user_id=g.user.id).order_by(Enrollment.enrolled_at.desc()).all()
    
    # Compile details of user activity
    courses_enrolled = len(enrollments)
    courses_completed = sum(1 for e in enrollments if e.completed)
    
    progress_map = {}
    total_lectures_completed = 0
    
    for e in enrollments:
        course = e.course
        total_lectures = len(course.lectures)
        if total_lectures == 0:
            progress_map[e.id] = 0
            continue
            
        lecture_ids = [l.id for l in course.lectures]
        completed_count = Progress.query.filter(
            Progress.user_id == g.user.id,
            Progress.lecture_id.in_(lecture_ids)
        ).count()
        
        progress_map[e.id] = int((completed_count / total_lectures) * 100)
        total_lectures_completed += completed_count
        
    return render_template(
        'dashboard.html',
        enrollments=enrollments,
        courses_enrolled=courses_enrolled,
        courses_completed=courses_completed,
        total_completed_lessons=total_lectures_completed,
        progress_map=progress_map
    )

@app.route('/materials')
def materials():
    from models import StudyMaterial
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    file_type = request.args.get('file_type', 'All').strip()
    
    # Build query
    query = StudyMaterial.query
    
    # Apply search filter
    if search_query:
        query = query.filter(StudyMaterial.title.like(f'%{search_query}%'))
    
    # Apply file type filter
    if file_type and file_type != 'All':
        query = query.filter_by(file_type=file_type)
    
    study_materials = query.all()
    
    return render_template(
        'materials.html', 
        materials=study_materials,
        search_query=search_query,
        selected_type=file_type
    )

@app.route('/materials/download/<int:material_id>')
def download_material(material_id):
    from models import StudyMaterial
    material = StudyMaterial.query.get_or_404(material_id)
    
    # In a real app, this would serve the file
    # For now, redirect to the file URL (external link or static file)
    return redirect(material.file_url)

@app.route('/materials/upload', methods=['POST'])
@login_required
def upload_material():
    if g.user.email != 'admin@nexora.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('materials'))
        
    title = request.form.get('title', '').strip()
    file_type = request.form.get('file_type', '').strip()
    category = request.form.get('category', '').strip()
    file_size = request.form.get('file_size', '').strip()
    file_url = request.form.get('file_url', '').strip()
    
    if not title or not file_type or not category or not file_size or not file_url:
        flash('Please fill in all upload fields.', 'danger')
        return redirect(url_for('materials'))
        
    from models import StudyMaterial
    new_material = StudyMaterial(
        title=title,
        file_type=file_type,
        category=category,
        file_size=file_size,
        file_url=file_url
    )
    db.session.add(new_material)
    db.session.commit()
    
    flash(f'Successfully uploaded and published: {title}!', 'success')
    return redirect(url_for('materials'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=g.user)

@app.route('/quiz/<int:course_id>')
@login_required
def quiz(course_id):
    from models import QuizQuestion
    course = Course.query.get_or_404(course_id)
    
    # Verify enrollment
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course_id).first()
    if not enrollment:
        flash('You must enroll in this course first.', 'warning')
        return redirect(url_for('course_details', slug=course.slug))
    
    questions = QuizQuestion.query.filter_by(course_id=course_id).all()
    return render_template('quiz.html', course=course, questions=questions)

@app.route('/quiz/<int:course_id>/submit', methods=['POST'])
@login_required
def submit_quiz(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Verify enrollment
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course_id).first()
    if not enrollment:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('courses'))
    
    from models import QuizQuestion
    questions = QuizQuestion.query.filter_by(course_id=course_id).all()
    
    correct_count = 0
    for q in questions:
        user_answer = request.form.get(f'question_{q.id}', '')
        if user_answer == q.correct_option:
            correct_count += 1
    
    score = int((correct_count / len(questions) * 100)) if questions else 0
    
    return render_template('quiz_result.html', course=course, score=score, total=len(questions), correct=correct_count)

@app.route('/certificate/<int:course_id>')
@login_required
def certificate(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Verify enrollment and completion
    enrollment = Enrollment.query.filter_by(user_id=g.user.id, course_id=course_id).first()
    if not enrollment or not enrollment.completed:
        flash('You must complete this course to get a certificate.', 'warning')
        return redirect(url_for('course_details', slug=course.slug))
    
    return render_template('certificate.html', user=g.user, course=course, now=datetime.now(timezone.utc))

def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('admin_login', next=request.url))
        if g.user.email != 'admin@nexora.com':
            flash('Unauthorized access. Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return view(**kwargs)
    return wrapped_view

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if g.user:
        if g.user.email == 'admin@nexora.com':
            return redirect(url_for('admin_dashboard'))
        
    next_url = request.args.get('next', '')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in all credentials fields.', 'danger')
            return render_template('admin/login.html', next=next_url)
            
        if email != 'admin@nexora.com':
            flash('Only administrator accounts can sign in here. Students should use the regular login portal.', 'danger')
            return render_template('admin/login.html', next=next_url)
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('admin/login.html', next=next_url)
            
        # Success log
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        
        flash('Welcome to the Admin Portal!', 'success')
        
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/login.html', next=next_url)

@app.route('/admin')
@admin_required
def admin_dashboard():
    courses = Course.query.order_by(Course.id.desc()).all()
    materials = StudyMaterial.query.order_by(StudyMaterial.id.desc()).all()
    
    courses_count = Course.query.count()
    lectures_count = Lecture.query.count()
    materials_count = StudyMaterial.query.count()
    enrollments_count = Enrollment.query.count()
    
    return render_template(
        'admin/dashboard.html',
        courses=courses,
        materials=materials,
        courses_count=courses_count,
        lectures_count=lectures_count,
        materials_count=materials_count,
        enrollments_count=enrollments_count
    )

@app.route('/admin/course/create', methods=['GET', 'POST'])
@admin_required
def admin_course_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration = request.form.get('duration', '').strip()
        price = float(request.form.get('price', 0.0))
        instructor = request.form.get('instructor', 'Nexora Academy').strip()
        gradient_start = request.form.get('gradient_start', '#4f46e5').strip()
        gradient_end = request.form.get('gradient_end', '#7c3aed').strip()
        skills = request.form.get('skills', '').strip()
        requirements = request.form.get('requirements', '').strip()
        
        # Check slug unique
        existing_course = Course.query.filter_by(slug=slug).first()
        if existing_course:
            flash(f"A course with slug '{slug}' already exists. Please choose a unique title or slug.", "danger")
            return render_template('admin/course_form.html')
            
        new_course = Course(
            title=title,
            slug=slug,
            description=description,
            category=category,
            difficulty=difficulty,
            duration=duration,
            price=price,
            instructor=instructor,
            gradient_start=gradient_start,
            gradient_end=gradient_end,
            skills=skills,
            requirements=requirements
        )
        db.session.add(new_course)
        db.session.commit()
        flash(f"Course '{title}' successfully created!", "success")
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/course_form.html', course=None)

@app.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration = request.form.get('duration', '').strip()
        price = float(request.form.get('price', 0.0))
        instructor = request.form.get('instructor', 'Nexora Academy').strip()
        gradient_start = request.form.get('gradient_start', '#4f46e5').strip()
        gradient_end = request.form.get('gradient_end', '#7c3aed').strip()
        skills = request.form.get('skills', '').strip()
        requirements = request.form.get('requirements', '').strip()
        
        # Check slug unique if changed
        if slug != course.slug:
            existing_course = Course.query.filter_by(slug=slug).first()
            if existing_course:
                flash(f"A course with slug '{slug}' already exists.", "danger")
                return render_template('admin/course_form.html', course=course)
        
        course.title = title
        course.slug = slug
        course.description = description
        course.category = category
        course.difficulty = difficulty
        course.duration = duration
        course.price = price
        course.instructor = instructor
        course.gradient_start = gradient_start
        course.gradient_end = gradient_end
        course.skills = skills
        course.requirements = requirements
        
        db.session.commit()
        flash(f"Course '{title}' successfully updated!", "success")
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/course_form.html', course=course)

@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
@admin_required
def admin_course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    title = course.title
    db.session.delete(course)
    db.session.commit()
    flash(f"Course '{title}' and all associated lectures/materials deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/course/<int:course_id>/lectures')
@admin_required
def admin_course_lectures(course_id):
    course = Course.query.get_or_404(course_id)
    lectures = Lecture.query.filter_by(course_id=course_id).order_by(Lecture.order_num).all()
    return render_template('admin/lectures.html', course=course, lectures=lectures)

@app.route('/admin/course/<int:course_id>/lecture/create', methods=['GET', 'POST'])
@admin_required
def admin_lecture_create(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        duration = request.form.get('duration', '').strip()
        video_url_input = request.form.get('video_url', '').strip()
        video_file = request.files.get('video_file')
        description = request.form.get('description', '').strip()
        order_num = int(request.form.get('order_num', 1))
        resources = request.form.get('resources', '').strip()

        try:
            video_url = save_uploaded_video(video_file)
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('admin/lecture_form.html', course=course, lecture=None, next_order_num=Lecture.query.filter_by(course_id=course_id).count() + 1)

        if not video_url:
            video_url = normalize_video_url(video_url_input)

        if not video_url:
            flash('Please upload a video file or provide a video URL.', 'danger')
            return render_template('admin/lecture_form.html', course=course, lecture=None, next_order_num=Lecture.query.filter_by(course_id=course_id).count() + 1)
        
        new_lecture = Lecture(
            course_id=course_id,
            title=title,
            duration=duration,
            video_url=video_url,
            description=description,
            order_num=order_num,
            resources=resources
        )
        db.session.add(new_lecture)
        db.session.commit()
        flash(f"Lecture '{title}' added to course curriculum.", "success")
        return redirect(url_for('admin_course_lectures', course_id=course_id))
        
    next_order_num = Lecture.query.filter_by(course_id=course_id).count() + 1
    return render_template('admin/lecture_form.html', course=course, lecture=None, next_order_num=next_order_num)

@app.route('/admin/course/<int:course_id>/lecture/<int:lecture_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_lecture_edit(course_id, lecture_id):
    course = Course.query.get_or_404(course_id)
    lecture = Lecture.query.filter_by(id=lecture_id, course_id=course_id).first_or_404()
    if request.method == 'POST':
        lecture.title = request.form.get('title', '').strip()
        lecture.duration = request.form.get('duration', '').strip()
        video_url_input = request.form.get('video_url', '').strip()
        video_file = request.files.get('video_file')
        lecture.description = request.form.get('description', '').strip()
        lecture.order_num = int(request.form.get('order_num', 1))
        lecture.resources = request.form.get('resources', '').strip()

        try:
            uploaded_video_url = save_uploaded_video(video_file)
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('admin/lecture_form.html', course=course, lecture=lecture)

        if uploaded_video_url:
            lecture.video_url = uploaded_video_url
        elif video_url_input:
            lecture.video_url = normalize_video_url(video_url_input)
        elif not lecture.video_url:
            flash('Please upload a video file or provide a video URL.', 'danger')
            return render_template('admin/lecture_form.html', course=course, lecture=lecture)
        
        db.session.commit()
        flash(f"Lecture '{lecture.title}' updated successfully.", "success")
        return redirect(url_for('admin_course_lectures', course_id=course_id))
        
    return render_template('admin/lecture_form.html', course=course, lecture=lecture)

@app.route('/admin/course/<int:course_id>/lecture/<int:lecture_id>/delete', methods=['POST'])
@admin_required
def admin_lecture_delete(course_id, lecture_id):
    lecture = Lecture.query.filter_by(id=lecture_id, course_id=course_id).first_or_404()
    title = lecture.title
    db.session.delete(lecture)
    db.session.commit()
    flash(f"Lecture '{title}' deleted from curriculum.", "success")
    return redirect(url_for('admin_course_lectures', course_id=course_id))

@app.route('/admin/material/create', methods=['GET', 'POST'])
@admin_required
def admin_material_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        file_type = request.form.get('file_type', '').strip()
        category = request.form.get('category', '').strip()
        file_size = request.form.get('file_size', '').strip()
        file_url = request.form.get('file_url', '').strip()
        course_id = request.form.get('course_id', '')
        
        c_id = int(course_id) if course_id else None
        
        new_material = StudyMaterial(
            title=title,
            file_type=file_type,
            category=category,
            file_size=file_size,
            file_url=file_url,
            course_id=c_id
        )
        db.session.add(new_material)
        db.session.commit()
        flash(f"Study resource '{title}' published successfully.", "success")
        return redirect(url_for('admin_dashboard'))
        
    courses = Course.query.order_by(Course.title).all()
    return render_template('admin/material_form.html', courses=courses, material=None)

@app.route('/admin/material/<int:material_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_material_edit(material_id):
    material = StudyMaterial.query.get_or_404(material_id)
    if request.method == 'POST':
        material.title = request.form.get('title', '').strip()
        material.file_type = request.form.get('file_type', '').strip()
        material.category = request.form.get('category', '').strip()
        material.file_size = request.form.get('file_size', '').strip()
        material.file_url = request.form.get('file_url', '').strip()
        course_id = request.form.get('course_id', '')
        
        material.course_id = int(course_id) if course_id else None
        
        db.session.commit()
        flash(f"Study material '{material.title}' updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
        
    courses = Course.query.order_by(Course.title).all()
    return render_template('admin/material_form.html', courses=courses, material=material)

@app.route('/admin/material/<int:material_id>/delete', methods=['POST'])
@admin_required
def admin_material_delete(material_id):
    material = StudyMaterial.query.get_or_404(material_id)
    title = material.title
    db.session.delete(material)
    db.session.commit()
    flash(f"Study resource '{title}' deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
