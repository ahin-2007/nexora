import io
import sys
import os
sys.path.append(r'c:\Users\AHIN\Desktop\github\learning-portal')

from app import app, db
from models import User, Course, Lecture, StudyMaterial, Enrollment

def test_admin_portal():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    client = app.test_client()
    
    print("[*] Starting Admin Portal Automated Verification...")
    
    # 1. Accessing /admin when not logged in should fail with 401
    resp = client.get('/admin')
    assert resp.status_code == 401
    assert b'Authentication required' in resp.data
    print("[OK] Correctly redirected/failed guest user trying to access /admin")
    
    # Let's create a test context and seed users
    with app.app_context():
        # Cleanup any leftover test course/materials
        existing_test_course = Course.query.filter_by(slug='test-admin-course').first()
        if existing_test_course:
            db.session.delete(existing_test_course)
            db.session.commit()
            
        existing_test_course_updated = Course.query.filter_by(slug='test-admin-course-updated').first()
        if existing_test_course_updated:
            db.session.delete(existing_test_course_updated)
            db.session.commit()

        # Ensure we have admin and normal user
        normal_user = User.query.filter_by(email="student@example.com").first()
        if not normal_user:
            normal_user = User(name="Test Student", email="student@example.com")
            normal_user.set_password("student123")
            db.session.add(normal_user)
            
        admin_user = User.query.filter_by(email="admin@nexora.com").first()
        if not admin_user:
            admin_user = User(name="Administrator", email="admin@nexora.com")
            admin_user.set_password("admin123")
            db.session.add(admin_user)
        
        db.session.commit()
        
        normal_user_id = normal_user.id
        admin_user_id = admin_user.id

    # 2. Access student login route with admin credentials - should fail with 400 and flag redirect
    resp = client.post('/login', data={'email': 'admin@nexora.com', 'password': 'admin123'})
    assert resp.status_code == 400
    assert resp.get_json()['redirect_to_admin_login'] is True
    print("[OK] Correctly blocked admin from student login page and redirected to admin login")

    # 3. Access admin login route with student credentials - should fail with 403
    resp = client.post('/admin/login', data={'email': 'student@example.com', 'password': 'student123'})
    assert resp.status_code == 403
    assert b'Only administrator accounts can sign in here' in resp.data
    print("[OK] Correctly blocked student from admin login page")

    # 4. Login as student, check authorization error when visiting /admin
    with client.session_transaction() as sess:
        sess['user_id'] = normal_user_id
        sess['user_name'] = "Test Student"
        sess['user_email'] = "student@example.com"
        
    resp = client.get('/admin')
    assert resp.status_code == 403
    assert b'Admin privileges required' in resp.data
    print("[OK] Correctly redirected/blocked regular student trying to access /admin")
    
    # 5. Login as admin via POST to /admin/login, check dashboard access
    client = app.test_client()
    resp = client.post('/admin/login', data={'email': 'admin@nexora.com', 'password': 'admin123'})
    assert resp.status_code == 200
    assert b'Welcome to the Admin Portal' in resp.data
    print("[OK] Successfully logged in and accessed Admin Dashboard via /admin/login")
    
    # 6. Create a course
    course_data = {
        'title': 'Test Admin Course',
        'slug': 'test-admin-course',
        'description': 'Automated test course description details',
        'category': 'Programming',
        'difficulty': 'Intermediate',
        'duration': '5h 15m',
        'price': '49.99',
        'instructor': 'Test Admin Instructor',
        'gradient_start': '#4f46e5',
        'gradient_end': '#7c3aed',
        'skills': 'Automation Testing, Flask',
        'requirements': 'Python basic understanding'
    }
    
    resp = client.post('/admin/course/create', data=course_data)
    assert resp.status_code == 201
    assert b'successfully created' in resp.data
    print("[OK] Successfully created a new course via the admin route")
    
    # Verify course is in the database
    with app.app_context():
        course = Course.query.filter_by(slug='test-admin-course').first()
        assert course is not None
        assert course.price == 49.99
        course_id = course.id
        print(f"[OK] Verified course exists in database with ID: {course_id}")
        
    # 7. Edit the course details
    edit_data = course_data.copy()
    edit_data['price'] = '79.99'
    edit_data['title'] = 'Test Admin Course Updated'
    resp = client.post(f'/admin/course/{course_id}/edit', data=edit_data)
    assert resp.status_code == 200
    assert b'successfully updated' in resp.data
    
    with app.app_context():
        course = db.session.get(Course, course_id)
        assert course.price == 79.99
        assert course.title == 'Test Admin Course Updated'
        print("[OK] Successfully edited course details")
        
    # 8. Add a lecture to the course
    lecture_data = {
        'title': 'Lecture 1: Introduction to Automation',
        'duration': '10:45',
        'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
        'description': 'Introduction description details here',
        'order_num': '1',
        'resources': '* [Google](https://google.com)'
    }
    resp = client.post(f'/admin/course/{course_id}/lecture/create', data=lecture_data)
    assert resp.status_code == 201
    assert b'added to course curriculum' in resp.data
    
    with app.app_context():
        lecture = Lecture.query.filter_by(course_id=course_id, order_num=1).first()
        assert lecture is not None
        assert lecture.duration == '10:45'
        lecture_id = lecture.id
        print(f"[OK] Successfully added lecture '{lecture.title}' (ID: {lecture_id})")
        
    # 9. Edit the lecture details
    edit_lecture_data = lecture_data.copy()
    edit_lecture_data['duration'] = '15:20'
    resp = client.post(f'/admin/course/{course_id}/lecture/{lecture_id}/edit', data=edit_lecture_data)
    assert resp.status_code == 200
    assert b'updated successfully' in resp.data
    
    with app.app_context():
        lecture = db.session.get(Lecture, lecture_id)
        assert lecture.duration == '15:20'
        print("[OK] Successfully edited lecture details")
 
    # 10. Upload a local lecture video file
    uploaded_lecture_data = {
        'title': 'Lecture 2: Uploaded Demo',
        'duration': '08:30',
        'video_url': '',
        'description': 'Uploaded video lecture description',
        'order_num': '2',
        'resources': '* [Docs](https://example.com)'
    }
    resp = client.post(
        f'/admin/course/{course_id}/lecture/create',
        data={**uploaded_lecture_data, 'video_file': (io.BytesIO(b'fake video bytes'), 'demo.mp4')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 201
    assert b'added to course curriculum' in resp.data

    with app.app_context():
        uploaded_lecture = Lecture.query.filter_by(course_id=course_id, title='Lecture 2: Uploaded Demo').first()
        assert uploaded_lecture is not None
        assert uploaded_lecture.video_url.startswith('/static/uploads/videos/')
        print("[OK] Successfully uploaded a lecture video file")
        
    # 11. Create study material
    material_data = {
        'title': 'Automation Practice Cheat Sheet',
        'file_type': 'PDF',
        'category': 'Programming',
        'file_size': '1.2 MB',
        'file_url': 'http://example.com/sheet.pdf',
        'course_id': str(course_id)
    }
    resp = client.post('/admin/material/create', data=material_data)
    assert resp.status_code == 201
    assert b'published successfully' in resp.data
    
    with app.app_context():
        material = StudyMaterial.query.filter_by(course_id=course_id).first()
        assert material is not None
        material_id = material.id
        print(f"[OK] Successfully uploaded study material (ID: {material_id})")
        
    # 12. Delete study material
    resp = client.post(f'/admin/material/{material_id}/delete')
    assert resp.status_code == 200
    
    with app.app_context():
        material = db.session.get(StudyMaterial, material_id)
        assert material is None
        print("[OK] Successfully deleted study material")
        
    # 13. Delete the course (cascading delete check)
    resp = client.post(f'/admin/course/{course_id}/delete')
    assert resp.status_code == 200
    
    with app.app_context():
        # Check course is deleted
        course = db.session.get(Course, course_id)
        assert course is None
        # Check lecture is deleted via cascade
        lecture = db.session.get(Lecture, lecture_id)
        assert lecture is None
        print("[OK] Successfully deleted course with cascade deletes on curriculum lectures")

    print("\n[OK] ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_admin_portal()
