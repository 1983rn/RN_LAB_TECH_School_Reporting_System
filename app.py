#!/usr/bin/env python3
"""
Malawi School Reporting System - Web Application
Flask-based web interface for school report generation

Created by: RN_LAB_TECH
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
import os
import sys
from datetime import datetime
import json
import hashlib

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from termly_report_generator import TermlyReportGenerator
from performance_analyzer import PerformanceAnalyzer
from school_database import SchoolDatabase

# Configure Flask app with explicit paths
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.secret_key = 'malawi_school_reporting_system_2025'

# Developer credentials
DEVELOPER_USERNAME = 'MAKONOKAya'
DEVELOPER_PASSWORD = 'NAMADEYIMKOLOWEKO1949'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    return 'user_id' in session and 'user_type' in session

def check_developer_auth():
    return session.get('user_type') == 'developer'

def check_subscription_status():
    """Check if school subscription is valid"""
    if session.get('user_type') == 'school':
        days_remaining = session.get('days_remaining', 0)
        if days_remaining <= 0:
            return False
    return True

@app.before_request
def before_request():
    """Check subscription status before each request"""
    # Skip subscription check for login, logout, and developer routes
    exempt_routes = ['login', 'api_login', 'logout', 'developer_dashboard']
    exempt_prefixes = ['/api/developer/', '/static/']
    
    if request.endpoint in exempt_routes:
        return
    
    for prefix in exempt_prefixes:
        if request.path.startswith(prefix):
            return
    
    # Check if user is logged in
    if not check_auth():
        return redirect(url_for('login'))
    
    # Check subscription status for schools
    if session.get('user_type') == 'school' and not check_subscription_status():
        session.clear()
        flash('Your subscription has expired. Please contact the administrator to renew.', 'error')
        return redirect(url_for('login'))

# Initialize system components
db = SchoolDatabase()
generator = TermlyReportGenerator(
    school_name="DEMO SECONDARY SCHOOL",
    school_address="P.O. Box 123, Lilongwe, Malawi",
    school_phone="+265 1 234 5678",
    school_email="demo@school.edu.mw"
)
analyzer = PerformanceAnalyzer("DEMO SECONDARY SCHOOL")

@app.route('/')
def index():
    """Main dashboard with form selection"""
    if not check_auth():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login authentication"""
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        user_type = data['user_type']
        
        if user_type == 'developer':
            if username == DEVELOPER_USERNAME and password == DEVELOPER_PASSWORD:
                session['user_id'] = 'developer'
                session['user_type'] = 'developer'
                session['username'] = username
                return jsonify({'success': True, 'redirect': '/developer-dashboard'})
        elif user_type == 'school':
            # Check school credentials
            school = db.authenticate_school(username, password)
            if school:
                session['user_id'] = school['school_id']
                session['user_type'] = 'school'
                session['username'] = username
                session['school_name'] = school['school_name']
                session['subscription_status'] = school['subscription_status']
                session['days_remaining'] = school['days_remaining']
                
                # Check if subscription is expired
                if school['days_remaining'] <= 0:
                    return jsonify({
                        'success': False, 
                        'message': 'Your subscription has expired. Please contact the administrator to renew your subscription.'
                    })
                
                return jsonify({'success': True, 'redirect': '/'})
        
        return jsonify({'success': False, 'message': 'Invalid credentials'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/developer-dashboard')
def developer_dashboard():
    """Developer dashboard"""
    if not check_developer_auth():
        return redirect(url_for('login'))
    return render_template('developer_dashboard.html')

@app.route('/form/<int:form_level>')
def form_data_entry(form_level):
    """Data entry page for specific form"""
    if form_level not in [1, 2, 3, 4]:
        return redirect(url_for('index'))
    
    subjects = ['Agriculture', 'Bible Knowledge', 'Biology', 'Chemistry', 
               'Chichewa', 'Computer Studies', 'English', 'Geography', 
               'History', 'Life Skills/SOS', 'Mathematics', 'Physics']
    
    # Get students for this form
    try:
        students = db.get_students_by_grade(form_level)
    except Exception as e:
        print(f"Error getting students: {e}")
        students = []
    
    # Get terms and academic years from settings or define defaults
    settings = db.get_school_settings() if hasattr(db, 'get_school_settings') else {}
    terms = settings.get('terms', ['Term 1', 'Term 2', 'Term 3'])
    academic_years = settings.get('academic_years', [f'{y}-{y+1}' for y in range(2020, 2031)])
    return render_template('form_data_entry.html', 
                         form_level=form_level, 
                         subjects=subjects, 
                         students=students,
                         terms=terms,
                         academic_years=academic_years)

@app.route('/report-generator')
def report_generator():
    """Report card generator page"""
    return render_template('report_generator.html')

@app.route('/ranking-analysis')
def ranking_analysis():
    """Ranking and analysis page"""
    return render_template('ranking_analysis.html')

@app.route('/settings')
def settings():
    """Settings page"""
    # Get current settings for terms and academic years
    settings_obj = db.get_school_settings() if hasattr(db, 'get_school_settings') else {}
    terms = settings_obj.get('terms', ['Term 1', 'Term 2', 'Term 3'])
    academic_years = settings_obj.get('academic_years', [f'{y}-{y+1}' for y in range(2020, 2031)])
    return render_template('settings.html', terms=terms, academic_years=academic_years, settings=settings_obj)

@app.route('/api/save-student-marks', methods=['POST'])
def api_save_student_marks():
    """Save student marks from data entry"""
    try:
        data = request.get_json()
        student_id = data['student_id']
        form_level = data['form_level']
        term = data['term']
        academic_year = data['academic_year']
        marks = data['marks']  # Dictionary of subject: mark
        
        # Save marks to database
        for subject, mark in marks.items():
            if mark is not None and str(mark).strip():
                mark_value = int(str(mark).strip())
                db.save_student_mark(student_id, subject, mark_value, term, academic_year, form_level)
        
        return jsonify({
            'success': True,
            'message': 'Marks saved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving marks: {str(e)}'
        })

@app.route('/api/get-student-marks', methods=['POST'])
def api_get_student_marks():
    """Get student marks for data entry form"""
    try:
        data = request.get_json()
        student_id = data['student_id']
        term = data['term']
        academic_year = data['academic_year']
        
        marks = db.get_student_marks(student_id, term, academic_year)
        
        return jsonify({
            'success': True,
            'marks': marks
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving marks: {str(e)}'
        })


# Generate report card for a single student
@app.route('/api/generate-report-card', methods=['POST'])
def api_generate_report_card():
    """Generate report card for selected student"""
    try:
        data = request.get_json()
        student_id = int(data['student_id'])
        term = data['term']
        academic_year = data['academic_year']
        report = generator.generate_progress_report(student_id, term, academic_year)
        if report:
            return jsonify({
                'success': True,
                'report': report,
                'message': f'Report generated for Student ID: {student_id}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No report data found for the specified student'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating report: {str(e)}'
        })

# Generate report cards for all students in all forms
@app.route('/api/generate-all-reports', methods=['POST'])
def api_generate_all_reports():
    """Generate report cards for all students in all forms"""
    try:
        data = request.get_json()
        term = data['term']
        academic_year = data['academic_year']
        all_reports = []
        for form_level in [1, 2, 3, 4]:
            students = db.get_students_by_grade(form_level)
            for student in students:
                student_id = student['student_id']
                report = generator.generate_progress_report(student_id, term, academic_year)
                if report:
                    all_reports.append({
                        'student_id': student_id,
                        'form_level': form_level,
                        'report': report
                    })
        if all_reports:
            return jsonify({
                'success': True,
                'reports': all_reports,
                'message': f'Generated reports for {len(all_reports)} students.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No report data found for any students.'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating all reports: {str(e)}'
        })


# Export report card as PDF for a single student
@app.route('/api/export-report-card', methods=['POST'])
def api_export_report_card():
    """Export report card as PDF file"""
    try:
        data = request.get_json()
        student_id = int(data['student_id'])
        term = data['term']
        academic_year = data['academic_year']
        
        # First check if student exists
        student = db.get_student_by_id(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
        
        # Check if student has marks for this term/year
        marks = db.get_student_marks(student_id, term, academic_year)
        if not marks:
            return jsonify({
                'success': False,
                'message': f'No marks found for {student["first_name"]} {student["last_name"]} in {term} {academic_year}'
            }), 400
        
        # Try to export the report
        filename = generator.export_progress_report(student_id, term, academic_year)
        
        if filename and os.path.exists(filename):
            try:
                mimetype = 'application/pdf' if filename.endswith('.pdf') else 'text/plain'
                return send_file(filename, as_attachment=True, download_name=os.path.basename(filename), mimetype=mimetype)
            except Exception as send_error:
                return jsonify({
                    'success': False,
                    'message': f'Error sending file: {str(send_error)}'
                }), 500
        else:
            # Try to get more specific error information
            report_text = generator.generate_progress_report(student_id, term, academic_year)
            if not report_text:
                return jsonify({
                    'success': False,
                    'message': 'Failed to generate report content'
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': 'Report generated but PDF export failed. Check reportlab installation.'
                }), 500
                
    except ImportError as ie:
        return jsonify({
            'success': False,
            'message': f'Missing required library: {str(ie)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting report: {str(e)}'
        }), 500

# Export all reports as a single PDF or ZIP (if supported by generator)
@app.route('/api/export-all-reports', methods=['POST'])
def api_export_all_reports():
    """Export all report cards as a single PDF or ZIP file"""
    try:
        data = request.get_json()
        term = data['term']
        academic_year = data['academic_year']
        # Try to use a batch export method if available, else zip individual PDFs
        if hasattr(generator, 'export_all_reports'):
            filename = generator.export_all_reports(term, academic_year)
        else:
            # Fallback: generate and zip all PDFs
            import zipfile
            from io import BytesIO
            pdf_files = []
            for form_level in [1, 2, 3, 4]:
                students = db.get_students_by_grade(form_level)
                for student in students:
                    student_id = student['student_id']
                    pdf = generator.export_progress_report(student_id, term, academic_year)
                    if pdf and os.path.exists(pdf):
                        pdf_files.append((f"Form{form_level}_{student_id}.pdf", pdf))
            if not pdf_files:
                return jsonify({'success': False, 'message': 'No reports to export.'}), 400
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                for arcname, filepath in pdf_files:
                    zipf.write(filepath, arcname)
            zip_buffer.seek(0)
            return send_file(zip_buffer, as_attachment=True, download_name='all_reports.zip', mimetype='application/zip')
        if filename and os.path.exists(filename):
            mimetype = 'application/pdf' if filename.endswith('.pdf') else 'application/zip'
            return send_file(filename, as_attachment=True, download_name=os.path.basename(filename), mimetype=mimetype)
        else:
            return jsonify({'success': False, 'message': 'Failed to export all reports.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error exporting all reports: {str(e)}'}), 500

@app.route('/api/get-student-rankings', methods=['POST'])
def api_get_student_rankings():
    """Get student rankings for analysis"""
    try:
        data = request.get_json()
        form_level = int(data['form_level'])
        term = data['term']
        academic_year = data['academic_year']
        
        rankings = analyzer.get_student_rankings(form_level, term, academic_year)
        
        return jsonify({
            'success': True,
            'rankings': rankings
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting rankings: {str(e)}'
        })

@app.route('/api/get-top-performers', methods=['POST'])
def api_get_top_performers():
    """Get top performers by category"""
    try:
        data = request.get_json()
        category = data['category']  # 'overall', 'sciences', 'humanities', 'languages'
        form_level = data.get('form_level')
        term = data['term']
        academic_year = data['academic_year']
        
        performers = analyzer.get_top_performers(category, form_level, term, academic_year)
        
        return jsonify({
            'success': True,
            'performers': performers
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting top performers: {str(e)}'
        })

@app.route('/api/export-rankings', methods=['POST'])
def api_export_rankings():
    """Export rankings to Excel"""
    try:
        data = request.get_json()
        form_level = int(data['form_level'])
        term = data['term']
        academic_year = data['academic_year']
        
        filename = analyzer.export_rankings_to_excel(form_level, term, academic_year)
        
        if filename and os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to export rankings'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting rankings: {str(e)}'
        })

@app.route('/api/add-student', methods=['POST'])
def api_add_student():
    """Add new student to database"""
    try:
        data = request.get_json()
        student_data = {
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'grade_level': int(data['form_level']),
            'date_of_birth': data.get('date_of_birth', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'parent_guardian_name': data.get('parent_guardian_name', ''),
            'parent_guardian_phone': data.get('parent_guardian_phone', ''),
            'parent_guardian_email': data.get('parent_guardian_email', '')
        }
        student_id = db.add_student(student_data)
        # Fetch the generated student_number
        student = db.get_student_by_id(student_id)
        student_number = student['student_number'] if student else None
        return jsonify({
            'success': True,
            'student_id': student_id,
            'student_number': student_number,
            'message': 'Student added successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error adding student: {str(e)}'
        })

@app.route('/api/get-all-students', methods=['GET'])
def api_get_all_students():
    """Get all students for report generator dropdown"""
    try:
        students = []
        for form_level in [1, 2, 3, 4]:
            form_students = db.get_students_by_grade(form_level)
            students.extend(form_students)
        
        return jsonify({
            'success': True,
            'students': students
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving students: {str(e)}'
        })



@app.route('/api/update-settings', methods=['POST'])
def api_update_settings():
    """API endpoint to update system settings"""
    try:
        data = request.get_json()
        

        # Accept terms and academic_years as part of settings
        terms = data.get('terms')
        academic_years = data.get('academic_years')

        # Save new settings (including new terms/years)
        db.update_school_settings(data)

        # No need to delete any marks: marks for new term/year will be empty by default
        # If a term or year is new, marks entry will start fresh for that selection
        # Old marks for previous terms/years are preserved in the database

        global generator, analyzer

        # Update generator with new settings
        generator = TermlyReportGenerator(
            school_name=data['school_name'],
            school_address=data['school_address'],
            school_phone=data['school_phone'],
            school_email=data['school_email']
        )
        
        # Update analyzer with new school name
        analyzer = PerformanceAnalyzer(data['school_name'])

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        })



@app.route('/api/get-subject-teachers', methods=['GET'])
def api_get_subject_teachers():
    """Get subject teachers by form level"""
    try:
        form_level = request.args.get('form_level', type=int)
        teachers = db.get_subject_teachers(form_level)
        return jsonify({
            'success': True,
            'teachers': teachers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting subject teachers: {str(e)}'
        })

@app.route('/api/update-subject-teacher', methods=['POST'])
def api_update_subject_teacher():
    """Update teacher for a subject in specific form"""
    try:
        data = request.get_json()
        subject = data['subject']
        form_level = int(data['form_level'])
        teacher_name = data['teacher_name']
        
        db.update_subject_teacher(subject, form_level, teacher_name)
        
        return jsonify({
            'success': True,
            'message': f'Updated teacher for {subject} Form {form_level}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating subject teacher: {str(e)}'
        })

@app.route('/api/test-export', methods=['POST'])
def api_test_export():
    """Test export functionality with detailed error reporting"""
    try:
        data = request.get_json()
        student_id = int(data['student_id'])
        term = data['term']
        academic_year = data['academic_year']
        
        # Check dependencies
        try:
            import reportlab
            reportlab_version = reportlab.__version__
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'ReportLab library not installed. Please install with: pip install reportlab'
            })
        
        # Check student exists
        student = db.get_student_by_id(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': f'Student with ID {student_id} not found'
            })
        
        # Check marks exist
        marks = db.get_student_marks(student_id, term, academic_year)
        if not marks:
            return jsonify({
                'success': False,
                'message': f'No marks found for {student["first_name"]} {student["last_name"]} in {term} {academic_year}. Please enter marks first.'
            })
        
        # Test report generation
        report_text = generator.generate_progress_report(student_id, term, academic_year)
        if not report_text:
            return jsonify({
                'success': False,
                'message': 'Failed to generate report text'
            })
        
        return jsonify({
            'success': True,
            'message': f'Export test passed. ReportLab v{reportlab_version} installed. Student: {student["first_name"]} {student["last_name"]}, Marks: {len(marks)} subjects',
            'student': student,
            'marks_count': len(marks),
            'reportlab_version': reportlab_version
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test failed: {str(e)}'
        })

@app.route('/api/delete-student', methods=['POST'])
def api_delete_student():
    """Delete a student and all their marks"""
    try:
        data = request.get_json()
        student_id = int(data['student_id'])
        
        # Get student info before deletion
        student = db.get_student_by_id(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
        
        # Delete student marks first
        db.delete_student_marks(student_id)
        
        # Delete student record
        db.delete_student(student_id)
        
        return jsonify({
            'success': True,
            'message': f'Student {student["first_name"]} {student["last_name"]} deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting student: {str(e)}'
        }), 500

@app.route('/api/developer/schools', methods=['GET'])
def api_get_schools():
    """Get all schools (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        schools = db.get_all_schools()
        return jsonify({
            'success': True,
            'schools': schools
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting schools: {str(e)}'
        })

@app.route('/api/developer/add-school', methods=['POST'])
def api_add_school():
    """Add new school (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        school_id = db.add_school(data)
        return jsonify({
            'success': True,
            'school_id': school_id,
            'message': 'School added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error adding school: {str(e)}'
        })

@app.route('/api/developer/update-school-status', methods=['POST'])
def api_update_school_status():
    """Update school status (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        db.update_school_status(data['school_id'], data['status'])
        return jsonify({
            'success': True,
            'message': 'School status updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating school status: {str(e)}'
        })

@app.route('/api/developer/delete-school', methods=['POST'])
def api_delete_school():
    """Delete school (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        school_id = data['school_id']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schools WHERE school_id = ?", (school_id,))
        
        return jsonify({
            'success': True,
            'message': 'School deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting school: {str(e)}'
        })

@app.route('/api/developer/grant-subscription', methods=['POST'])
def api_grant_subscription():
    """Grant subscription to school (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        school_id = data['school_id']
        months = data.get('months', 12)
        
        db.grant_subscription(school_id, months)
        return jsonify({
            'success': True,
            'message': f'Granted {months} months subscription successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error granting subscription: {str(e)}'
        })

@app.route('/api/developer/send-reminders', methods=['POST'])
def api_send_reminders():
    """Send subscription reminders to all schools (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Update days remaining first
        db.update_days_remaining()
        
        # Send reminders
        count = db.send_subscription_reminder()
        return jsonify({
            'success': True,
            'message': f'Sent reminders to {count} schools'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error sending reminders: {str(e)}'
        })

@app.route('/api/developer/schools-to-lock', methods=['GET'])
def api_schools_to_lock():
    """Get schools that should be locked (Developer only)"""
    if not check_developer_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Update days remaining first
        db.update_days_remaining()
        
        schools = db.get_schools_to_lock()
        return jsonify({
            'success': True,
            'schools': schools
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting schools to lock: {str(e)}'
        })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Set debug based on environment
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
