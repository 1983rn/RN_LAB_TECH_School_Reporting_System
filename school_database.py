#!/usr/bin/env python3
"""
School Reporting Database System
Main application for managing student records, grades, and reports
With separate tracking for Report Card items vs Internal Assessment items
Created: 2025-08-06
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from typing import List, Dict, Optional, Tuple
import logging

class SchoolDatabase:
    """Main class for managing school database operations"""
    
    def __init__(self, db_path: str = "school_reports.db"):
        """Initialize database connection and setup logging"""
        self.db_path = db_path
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('school_database.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize the database with schema if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_number TEXT UNIQUE,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        date_of_birth TEXT,
                        grade_level INTEGER NOT NULL,
                        email TEXT,
                        phone TEXT,
                        address TEXT,
                        parent_guardian_name TEXT,
                        parent_guardian_phone TEXT,
                        parent_guardian_email TEXT,
                        status TEXT DEFAULT 'Active',
                        date_enrolled TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS student_marks (
                        mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        subject TEXT NOT NULL,
                        mark INTEGER NOT NULL,
                        grade TEXT NOT NULL,
                        term TEXT NOT NULL,
                        academic_year TEXT NOT NULL,
                        form_level INTEGER NOT NULL,
                        date_entered TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students (student_id),
                        UNIQUE(student_id, subject, term, academic_year)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS school_settings (
                        setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_name TEXT,
                        school_address TEXT,
                        school_phone TEXT,
                        school_email TEXT,
                        pta_fund TEXT,
                        next_term_begins TEXT,
                        boys_uniform TEXT,
                        girls_uniform TEXT,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subject_teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT NOT NULL,
                        form_level INTEGER NOT NULL,
                        teacher_name TEXT NOT NULL,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(subject, form_level)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS school_fees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pta_fund TEXT,
                        sdf_fund TEXT,
                        boarding_fee TEXT,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schools (
                        school_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_name TEXT NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        subscription_status TEXT DEFAULT 'trial',
                        subscription_start_date TEXT,
                        subscription_end_date TEXT,
                        days_remaining INTEGER DEFAULT 90,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_login TEXT
                    )
                """)
                
                # Add subscription columns to existing schools table if they don't exist
                try:
                    cursor.execute("ALTER TABLE schools ADD COLUMN subscription_status TEXT DEFAULT 'trial'")
                except:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE schools ADD COLUMN subscription_start_date TEXT")
                except:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE schools ADD COLUMN subscription_end_date TEXT")
                except:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE schools ADD COLUMN days_remaining INTEGER DEFAULT 90")
                except:
                    pass  # Column already exists
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subscription_notifications (
                        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER,
                        message TEXT NOT NULL,
                        notification_type TEXT DEFAULT 'reminder',
                        sent_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        is_read INTEGER DEFAULT 0,
                        FOREIGN KEY (school_id) REFERENCES schools (school_id)
                    )
                """)
                
                # Update existing schools with default subscription values
                cursor.execute("""
                    UPDATE schools 
                    SET subscription_status = 'trial', days_remaining = 90 
                    WHERE subscription_status IS NULL OR subscription_status = ''
                """)
                
                # Insert default settings if none exist
                cursor.execute("SELECT COUNT(*) FROM school_settings")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO school_settings 
                        (school_name, school_address, school_phone, school_email, pta_fund, next_term_begins, boys_uniform, girls_uniform)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "DEMO SECONDARY SCHOOL",
                        "P.O. Box 123, Lilongwe, Malawi",
                        "+265 1 234 5678",
                        "demo@school.edu.mw",
                        "MK 50,000",
                        "To be announced",
                        "White shirt, black trousers, black shoes",
                        "White blouse, black skirt, black shoes"
                    ))
                
                # Insert default fees if none exist
                cursor.execute("SELECT COUNT(*) FROM school_fees")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO school_fees (pta_fund, sdf_fund, boarding_fee)
                        VALUES (?, ?, ?)
                    """, ("MK 50,000", "MK 30,000", "MK 150,000"))
                
                # Insert default subject teachers if none exist
                cursor.execute("SELECT COUNT(*) FROM subject_teachers")
                if cursor.fetchone()[0] == 0:
                    subjects = ['Agriculture', 'Bible Knowledge', 'Biology', 'Chemistry', 
                               'Chichewa', 'Computer Studies', 'English', 'Geography', 
                               'History', 'Life Skills/SOS', 'Mathematics', 'Physics']
                    for form_level in [1, 2, 3, 4]:
                        for subject in subjects:
                            cursor.execute("""
                                INSERT INTO subject_teachers (subject, form_level, teacher_name)
                                VALUES (?, ?, ?)
                            """, (subject, form_level, f"{subject} Teacher F{form_level}"))
                
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def create_schema(self, conn):
        """Create database schema from SQL file"""
        try:
            with open('database_schema.sql', 'r') as file:
                schema_sql = file.read()
                conn.executescript(schema_sql)
        except FileNotFoundError:
            self.logger.error("database_schema.sql file not found!")
            raise
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _get_next_student_serial_number(self) -> str:
        """Generate the next student serial number"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(CAST(student_number AS INTEGER)) FROM students")
                max_num = cursor.fetchone()[0]
                if max_num is None:
                    return "0001"
                else:
                    return f"{max_num + 1:04d}"
        except Exception as e:
            self.logger.error(f"Error generating next student serial number: {e}")
            # Fallback in case of error
            return "0000"

    # STUDENT MANAGEMENT METHODS
    def add_student(self, student_data: Dict, school_id: int = None) -> int:
        """Add a new student to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Generate new student serial number
                student_serial_number = self._get_next_student_serial_number()
                
                cursor.execute("""
                    INSERT INTO students (
                        student_number, first_name, last_name, date_of_birth,
                        grade_level, email, phone, address, parent_guardian_name,
                        parent_guardian_phone, parent_guardian_email, school_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_serial_number,
                    student_data.get('first_name'),
                    student_data.get('last_name'),
                    student_data.get('date_of_birth'),
                    student_data.get('grade_level'),
                    student_data.get('email'),
                    student_data.get('phone'),
                    student_data.get('address'),
                    student_data.get('parent_guardian_name'),
                    student_data.get('parent_guardian_phone'),
                    student_data.get('parent_guardian_email'),
                    school_id
                ))
                student_id = cursor.lastrowid
                self.logger.info(f"Added student: {student_data.get('first_name')} {student_data.get('last_name')} (ID: {student_id}, Ser No: {student_serial_number})")
                return student_id
        except Exception as e:
            self.logger.error(f"Error adding student: {e}")
            raise
    
    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student information by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving student {student_id}: {e}")
            raise
    
    def get_students_by_grade(self, grade_level: int, school_id: int = None) -> List[Dict]:
        """Get all students in a specific grade level for a specific school"""
        try:
            with self.get_connection() as conn:
                if school_id:
                    df = pd.read_sql_query(
                        "SELECT * FROM students WHERE grade_level = ? AND status = 'Active' AND school_id = ? ORDER BY first_name, last_name",
                        conn, params=(grade_level, school_id)
                    )
                else:
                    df = pd.read_sql_query(
                        "SELECT * FROM students WHERE grade_level = ? AND status = 'Active' ORDER BY first_name, last_name",
                        conn, params=(grade_level,)
                    )
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error retrieving students for grade {grade_level}: {e}")
            raise
    
    def update_student(self, student_id: int, first_name: str, last_name: str):
        """Update student's first and last name"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE students
                    SET first_name = ?, last_name = ?
                    WHERE student_id = ?
                """, (first_name, last_name, student_id))
                self.logger.info(f"Updated student {student_id} to {first_name} {last_name}")
        except Exception as e:
            self.logger.error(f"Error updating student {student_id}: {e}")
            raise
    
    # ASSESSMENT TYPE MANAGEMENT
    def get_report_card_assessment_types(self) -> List[Dict]:
        """Get assessment types that appear on report cards"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM assessment_types WHERE show_on_report_card = TRUE ORDER BY type_name",
                    conn
                )
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error retrieving report card assessment types: {e}")
            raise
    
    def get_internal_tracking_assessment_types(self) -> List[Dict]:
        """Get assessment types for internal tracking only"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM assessment_types WHERE is_internal_tracking = TRUE ORDER BY type_name",
                    conn
                )
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error retrieving internal tracking assessment types: {e}")
            raise
    
    # TEACHER MANAGEMENT METHODS
    def add_teacher(self, teacher_data: Dict) -> int:
        """Add a new teacher to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO teachers (
                        employee_id, first_name, last_name, email, phone, department
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    teacher_data.get('employee_id'),
                    teacher_data.get('first_name'),
                    teacher_data.get('last_name'),
                    teacher_data.get('email'),
                    teacher_data.get('phone'),
                    teacher_data.get('department')
                ))
                teacher_id = cursor.lastrowid
                self.logger.info(f"Added teacher: {teacher_data.get('first_name')} {teacher_data.get('last_name')} (ID: {teacher_id})")
                return teacher_id
        except Exception as e:
            self.logger.error(f"Error adding teacher: {e}")
            raise
    
    # SUBJECT MANAGEMENT METHODS
    def add_subject(self, subject_data: Dict) -> int:
        """Add a new subject to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO subjects (subject_code, subject_name, description, grade_level, credits)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    subject_data.get('subject_code'),
                    subject_data.get('subject_name'),
                    subject_data.get('description'),
                    subject_data.get('grade_level'),
                    subject_data.get('credits', 1.0)
                ))
                subject_id = cursor.lastrowid
                self.logger.info(f"Added subject: {subject_data.get('subject_name')} (ID: {subject_id})")
                return subject_id
        except Exception as e:
            self.logger.error(f"Error adding subject: {e}")
            raise
    
    # GRADE MANAGEMENT METHODS
    def add_grade(self, grade_data: Dict) -> int:
        """Add a grade record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate percentage and letter grade
                points_earned = grade_data.get('points_earned')
                points_possible = grade_data.get('points_possible')
                percentage = (points_earned / points_possible * 100) if points_possible > 0 else 0
                letter_grade = self.calculate_letter_grade(percentage)
                
                cursor.execute("""
                    INSERT INTO grades (
                        student_id, assessment_id, points_earned, points_possible,
                        percentage, letter_grade, comments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    grade_data.get('student_id'),
                    grade_data.get('assessment_id'),
                    points_earned,
                    points_possible,
                    percentage,
                    letter_grade,
                    grade_data.get('comments')
                ))
                grade_id = cursor.lastrowid
                self.logger.info(f"Added grade record (ID: {grade_id})")
                return grade_id
        except Exception as e:
            self.logger.error(f"Error adding grade: {e}")
            raise
    
    def calculate_letter_grade(self, percentage: float) -> str:
        """Calculate letter grade based on percentage"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT letter_grade FROM grade_scale 
                    WHERE ? BETWEEN min_percentage AND max_percentage
                """, (percentage,))
                result = cursor.fetchone()
                return result[0] if result else 'F'
        except Exception as e:
            self.logger.error(f"Error calculating letter grade: {e}")
            return 'F'
    
    def save_student_mark(self, student_id: int, subject: str, mark: int, term: str, academic_year: str, form_level: int, school_id: int = None):
        """Save student mark for a subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate grade based on form level
                grade = self.calculate_grade(mark, form_level)
                
                # Insert or update mark
                cursor.execute("""
                    INSERT OR REPLACE INTO student_marks 
                    (student_id, subject, mark, grade, term, academic_year, form_level, date_entered, school_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (student_id, subject, mark, grade, term, academic_year, form_level, datetime.now().isoformat(), school_id))
                
                self.logger.info(f"Saved mark for student {student_id}, subject {subject}: {mark}")
                
        except Exception as e:
            self.logger.error(f"Error saving student mark: {e}")
            raise
    
    def get_student_marks(self, student_id: int, term: str, academic_year: str, school_id: int = None) -> Dict:
        """Get all marks for a student in a term"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("""
                        SELECT subject, mark, grade FROM student_marks 
                        WHERE student_id = ? AND term = ? AND academic_year = ? AND school_id = ?
                    """, (student_id, term, academic_year, school_id))
                else:
                    cursor.execute("""
                        SELECT subject, mark, grade FROM student_marks 
                        WHERE student_id = ? AND term = ? AND academic_year = ?
                    """, (student_id, term, academic_year))
                
                marks = {}
                for row in cursor.fetchall():
                    marks[row[0]] = {'mark': row[1], 'grade': row[2]}
                
                return marks
                
        except Exception as e:
            self.logger.error(f"Error retrieving student marks: {e}")
            raise
    
    def calculate_grade(self, mark: int, form_level: int) -> str:
        """Calculate grade based on mark and form level"""
        if form_level in [1, 2]:  # Junior forms
            if mark >= 80: return 'A'
            elif mark >= 70: return 'B'
            elif mark >= 60: return 'C'
            elif mark >= 50: return 'D'
            else: return 'F'
        else:  # Senior forms (3, 4)
            if mark >= 75: return '1'
            elif mark >= 70: return '2'
            elif mark >= 65: return '3'
            elif mark >= 60: return '4'
            elif mark >= 55: return '5'
            elif mark >= 50: return '6'
            elif mark >= 45: return '7'
            elif mark >= 40: return '8'
            else: return '9'
    
    def determine_pass_fail_status(self, passed_subjects: int, english_passed: bool) -> str:
        """Determine overall pass/fail status based on school criteria"""
        # Student must pass at least 6 subjects AND English to be declared PASS
        if passed_subjects >= 6 and english_passed:
            return 'PASS'
        else:
            return 'FAIL'
    
    def get_status_reason(self, passed_subjects: int, english_passed: bool) -> str:
        """Get explanation for pass/fail status"""
        if passed_subjects >= 6 and english_passed:
            return 'Passed 6 or more subjects including English'
        elif passed_subjects >= 6 and not english_passed:
            return 'Failed English (English is mandatory for pass)'
        elif passed_subjects < 6 and english_passed:
            return f'Passed only {passed_subjects} subjects (minimum 6 required)'
        else:
            return f'Passed only {passed_subjects} subjects and failed English'
    
    # REPORT GENERATION METHODS
    def generate_termly_report_card(self, student_id: int, term: str, academic_year: str = '2024-2025') -> Dict:
        """Generate termly school report card with end-of-term exam marks and teacher names"""
        try:
            with self.get_connection() as conn:
                # Get student info
                student = self.get_student_by_id(student_id)
                if not student:
                    raise ValueError(f"Student with ID {student_id} not found")
                
                # Get term exam grades with teacher names (only end-of-term exams)
                grades_query = """
                    SELECT 
                        s.subject_name,
                        s.subject_code,
                        g.percentage,
                        g.letter_grade,
                        t.first_name || ' ' || t.last_name as teacher_name,
                        g.comments,
                        g.date_graded
                    FROM grades g
                    JOIN assessments a ON g.assessment_id = a.assessment_id
                    JOIN assessment_types at ON a.type_id = at.type_id
                    JOIN class_assignments ca ON a.assignment_id = ca.assignment_id
                    JOIN subjects s ON ca.subject_id = s.subject_id
                    JOIN teachers t ON ca.teacher_id = t.teacher_id
                    WHERE g.student_id = ? 
                    AND at.show_on_report_card = TRUE
                    AND at.type_name = ?
                    AND ca.academic_year = ?
                    AND ca.semester = ?
                    AND s.grade_level = ?
                    ORDER BY 
                        CASE s.subject_name
                            WHEN 'Agriculture' THEN 1
                            WHEN 'Biology' THEN 2
                            WHEN 'Bible Knowledge' THEN 3
                            WHEN 'Chemistry' THEN 4
                            WHEN 'Chichewa' THEN 5
                            WHEN 'Computer Studies' THEN 6
                            WHEN 'English' THEN 7
                            WHEN 'Geography' THEN 8
                            WHEN 'History' THEN 9
                            WHEN 'Life Skills/SOS' THEN 10
                            WHEN 'Mathematics' THEN 11
                            WHEN 'Physics' THEN 12
                            ELSE 13
                        END
                """
                
                term_exam_type = f"{term} Exam"  # e.g., "Term 1 Exam"
                
                grades_df = pd.read_sql_query(grades_query, conn, params=(
                    student_id, term_exam_type, academic_year, term, student['grade_level']
                ))
                
                # Get attendance summary for the term
                attendance_query = """
                    SELECT 
                        COUNT(*) as total_days,
                        SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
                        SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
                        SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days,
                        SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused_days
                    FROM attendance a
                    JOIN class_assignments ca ON a.assignment_id = ca.assignment_id
                    WHERE a.student_id = ?
                    AND ca.academic_year = ?
                    AND ca.semester = ?
                """
                attendance_df = pd.read_sql_query(attendance_query, conn, params=(student_id, academic_year, term))
                
                # Calculate overall statistics
                if not grades_df.empty:
                    overall_average = grades_df['percentage'].mean()
                    total_subjects = len(grades_df)
                    passed_subjects = len(grades_df[grades_df['percentage'] >= 50])
                    
                    # Check if English is passed (critical requirement)
                    english_grade = grades_df[grades_df['subject_name'] == 'English']
                    english_passed = False
                    english_percentage = 0
                    
                    if not english_grade.empty:
                        english_percentage = english_grade.iloc[0]['percentage']
                        english_passed = english_percentage >= 50
                    
                    # Determine overall pass/fail status
                    # Student must pass at least 6 subjects AND English to be declared PASS
                    overall_status = self.determine_pass_fail_status(passed_subjects, english_passed)
                    
                else:
                    overall_average = 0
                    total_subjects = 0
                    passed_subjects = 0
                    english_passed = False
                    english_percentage = 0
                    overall_status = 'FAIL'
                
                return {
                    'report_type': f'{term} School Report Card',
                    'academic_year': academic_year,
                    'term': term,
                    'student_info': student,
                    'subject_grades': grades_df.to_dict('records'),
                    'attendance_summary': attendance_df.to_dict('records')[0] if not attendance_df.empty else {},
                    'overall_statistics': {
                        'overall_average': round(overall_average, 1),
                        'total_subjects': total_subjects,
                        'passed_subjects': passed_subjects,
                        'english_passed': english_passed,
                        'english_percentage': round(english_percentage, 1),
                        'overall_grade': self.calculate_letter_grade(overall_average),
                        'overall_status': overall_status,
                        'status_reason': self.get_status_reason(passed_subjects, english_passed)
                    },
                    'generated_date': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error generating termly report card: {e}")
            raise
    
    def generate_internal_tracking_report(self, student_id: int, academic_year: str = None) -> Dict:
        """Generate internal tracking report showing quiz, homework, projects, etc."""
        try:
            with self.get_connection() as conn:
                # Get student info
                student = self.get_student_by_id(student_id)
                if not student:
                    raise ValueError(f"Student with ID {student_id} not found")
                
                # Get internal tracking grades only (is_internal_tracking = TRUE)
                grades_query = """
                    SELECT 
                        s.subject_name, 
                        s.subject_code, 
                        at.type_name as assessment_type,
                        g.percentage, 
                        g.letter_grade,
                        a.assessment_name, 
                        g.date_graded, 
                        g.comments,
                        g.points_earned,
                        g.points_possible
                    FROM grades g
                    JOIN assessments a ON g.assessment_id = a.assessment_id
                    JOIN assessment_types at ON a.type_id = at.type_id
                    JOIN class_assignments ca ON a.assignment_id = ca.assignment_id
                    JOIN subjects s ON ca.subject_id = s.subject_id
                    WHERE g.student_id = ? 
                    AND at.is_internal_tracking = TRUE
                    ORDER BY s.subject_name, g.date_graded DESC
                """
                params = [student_id]
                
                if academic_year:
                    grades_query += " AND ca.academic_year = ?"
                    params.append(academic_year)
                
                internal_grades_df = pd.read_sql_query(grades_query, conn, params=params)
                
                return {
                    'report_type': 'Internal Tracking Report',
                    'student_info': student,
                    'internal_assessments': internal_grades_df.to_dict('records'),
                    'generated_date': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error generating internal tracking report: {e}")
            raise
    
    def generate_comprehensive_teacher_report(self, student_id: int, academic_year: str = None) -> Dict:
        """Generate comprehensive report for teachers showing both report card and internal tracking"""
        try:
            report_card_data = self.generate_official_report_card(student_id, academic_year)
            internal_data = self.generate_internal_tracking_report(student_id, academic_year)
            
            return {
                'report_type': 'Comprehensive Teacher Report',
                'student_info': report_card_data['student_info'],
                'official_report_card': report_card_data['report_card_grades'],
                'internal_assessments': internal_data['internal_assessments'],
                'attendance_summary': report_card_data['attendance_summary'],
                'generated_date': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating comprehensive teacher report: {e}")
            raise
    
    def generate_class_summary(self, assignment_id: int, report_type: str = 'official') -> Dict:
        """Generate class summary report (official or internal)"""
        try:
            with self.get_connection() as conn:
                if report_type == 'official':
                    condition = "AND at.show_on_report_card = TRUE"
                elif report_type == 'internal':
                    condition = "AND at.is_internal_tracking = TRUE"
                else:
                    condition = ""  # All assessments
                
                query = f"""
                    SELECT 
                        s.student_number,
                        s.first_name,
                        s.last_name,
                        AVG(g.percentage) as average_grade,
                        COUNT(g.grade_id) as total_assessments
                    FROM students s
                    JOIN enrollments e ON s.student_id = e.student_id
                    LEFT JOIN grades g ON s.student_id = g.student_id
                    LEFT JOIN assessments a ON g.assessment_id = a.assessment_id
                    LEFT JOIN assessment_types at ON a.type_id = at.type_id
                    WHERE e.assignment_id = ? AND e.status = 'Enrolled'
                    {condition}
                    GROUP BY s.student_id
                    ORDER BY s.last_name, s.first_name
                """
                df = pd.read_sql_query(query, conn, params=(assignment_id,))
                return {
                    'report_type': f'Class Summary - {report_type.title()}',
                    'class_data': df.to_dict('records'),
                    'generated_date': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error generating class summary: {e}")
            raise
    
    # UTILITY METHODS
    def backup_database(self, backup_path: str = None):
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"school_reports_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def export_report_to_excel(self, report_data: Dict, output_file: str):
        """Export report data to Excel file"""
        try:
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # Student info sheet
                student_df = pd.DataFrame([report_data['student_info']])
                student_df.to_excel(writer, sheet_name='Student Info', index=False)
                
                # Report card grades (if exists)
                if 'report_card_grades' in report_data:
                    report_df = pd.DataFrame(report_data['report_card_grades'])
                    report_df.to_excel(writer, sheet_name='Report Card', index=False)
                
                # Internal assessments (if exists)
                if 'internal_assessments' in report_data:
                    internal_df = pd.DataFrame(report_data['internal_assessments'])
                    internal_df.to_excel(writer, sheet_name='Internal Tracking', index=False)
                
                # Attendance summary (if exists)
                if 'attendance_summary' in report_data and report_data['attendance_summary']:
                    attendance_df = pd.DataFrame([report_data['attendance_summary']])
                    attendance_df.to_excel(writer, sheet_name='Attendance', index=False)
                
            self.logger.info(f"Report exported to {output_file}")
        except Exception as e:
            self.logger.error(f"Error exporting report to Excel: {e}")
            raise
    
    def get_school_settings(self) -> Dict:
        """Get current school settings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM school_settings ORDER BY setting_id DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error retrieving school settings: {e}")
            return {}
    
    def get_student_position_and_points(self, student_id: int, term: str, academic_year: str, form_level: int, school_id: int = None) -> Dict:
        """Calculate student position in class and aggregate points"""
        try:
            with self.get_connection() as conn:
                # Get all students' averages in the same form (school-specific)
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("""
                        SELECT s.student_id, s.first_name, s.last_name, AVG(sm.mark) as average
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ? AND s.school_id = ?
                        GROUP BY s.student_id
                        ORDER BY average DESC
                    """, (form_level, term, academic_year, school_id))
                else:
                    cursor.execute("""
                        SELECT s.student_id, s.first_name, s.last_name, AVG(sm.mark) as average
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ?
                        GROUP BY s.student_id
                        ORDER BY average DESC
                    """, (form_level, term, academic_year))
                
                rankings = cursor.fetchall()
                position = 1
                
                for i, (sid, fname, lname, avg) in enumerate(rankings):
                    if sid == student_id:
                        position = i + 1
                        break
                
                # Calculate aggregate points (best 6 subjects for senior forms)
                if school_id:
                    cursor.execute("""
                        SELECT mark FROM student_marks 
                        WHERE student_id = ? AND term = ? AND academic_year = ? AND school_id = ?
                        ORDER BY mark DESC
                        LIMIT 6
                    """, (student_id, term, academic_year, school_id))
                else:
                    cursor.execute("""
                        SELECT mark FROM student_marks 
                        WHERE student_id = ? AND term = ? AND academic_year = ?
                        ORDER BY mark DESC
                        LIMIT 6
                    """, (student_id, term, academic_year))
                
                best_marks = [row[0] for row in cursor.fetchall()]
                # Convert marks to grade points for aggregate calculation
                if form_level >= 3:
                    grade_points = []
                    for mark in best_marks:
                        grade = self.calculate_grade(mark, form_level)
                        grade_points.append(int(grade) if grade.isdigit() else 9)
                    aggregate_points = sum(grade_points)
                else:
                    aggregate_points = sum(best_marks) if best_marks else 0
                
                return {
                    'position': position,
                    'aggregate_points': aggregate_points,
                    'total_students': len(rankings)
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating position and points: {e}")
            return {'position': 0, 'aggregate_points': 0, 'total_students': 0}
    
    def get_student_rankings(self, form_level: int, term: str, academic_year: str, school_id: int = None) -> List[Dict]:
        """Get student rankings for a form level"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("""
                        SELECT s.student_id, s.first_name, s.last_name, 
                               AVG(sm.mark) as average,
                               COUNT(CASE WHEN sm.mark >= 50 THEN 1 END) as subjects_passed
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ? AND s.school_id = ?
                        GROUP BY s.student_id
                        ORDER BY average DESC
                    """, (form_level, term, academic_year, school_id))
                else:
                    cursor.execute("""
                        SELECT s.student_id, s.first_name, s.last_name, 
                               AVG(sm.mark) as average,
                               COUNT(CASE WHEN sm.mark >= 50 THEN 1 END) as subjects_passed
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ?
                        GROUP BY s.student_id
                        ORDER BY average DESC
                    """, (form_level, term, academic_year))
                
                rankings = []
                for row in cursor.fetchall():
                    student_id, first_name, last_name, average, subjects_passed = row
                    
                    # Check if English is passed (school-specific)
                    if school_id:
                        cursor.execute("""
                            SELECT mark FROM student_marks 
                            WHERE student_id = ? AND subject = 'English' AND term = ? AND academic_year = ? AND school_id = ?
                        """, (student_id, term, academic_year, school_id))
                    else:
                        cursor.execute("""
                            SELECT mark FROM student_marks 
                            WHERE student_id = ? AND subject = 'English' AND term = ? AND academic_year = ?
                        """, (student_id, term, academic_year))
                    
                    english_result = cursor.fetchone()
                    english_passed = english_result and english_result[0] >= 50
                    
                    # Determine status
                    status = self.determine_pass_fail_status(subjects_passed, english_passed)
                    grade = self.calculate_grade(int(average), form_level)
                    
                    rankings.append({
                        'name': f"{first_name} {last_name}",
                        'average': average,
                        'grade': grade,
                        'subjects_passed': subjects_passed,
                        'status': status
                    })
                
                return rankings
                
        except Exception as e:
            self.logger.error(f"Error getting student rankings: {e}")
            return []
    
    def get_top_performers(self, category: str, form_level: int, term: str, academic_year: str, school_id: int = None) -> List[Dict]:
        """Get top performers by category"""
        try:
            if category == 'overall':
                return self.get_student_rankings(form_level, term, academic_year, school_id)[:10]
            
            # Define subject groups
            subject_groups = {
                'sciences': ['Agriculture', 'Biology', 'Chemistry', 'Computer Studies', 'Mathematics', 'Physics'],
                'humanities': ['Bible Knowledge', 'Geography', 'History', 'Life Skills/SOS'],
                'languages': ['English', 'Chichewa']
            }
            
            if category not in subject_groups:
                return []
            
            subjects = subject_groups[category]
            placeholders = ','.join(['?' for _ in subjects])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute(f"""
                        SELECT s.student_id, s.first_name, s.last_name, AVG(sm.mark) as average
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ? AND s.school_id = ?
                        AND sm.subject IN ({placeholders})
                        GROUP BY s.student_id
                        ORDER BY average DESC
                        LIMIT 10
                    """, (form_level, term, academic_year, school_id, *subjects))
                else:
                    cursor.execute(f"""
                        SELECT s.student_id, s.first_name, s.last_name, AVG(sm.mark) as average
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.term = ? AND sm.academic_year = ?
                        AND sm.subject IN ({placeholders})
                        GROUP BY s.student_id
                        ORDER BY average DESC
                        LIMIT 10
                    """, (form_level, term, academic_year, *subjects))
                
                performers = []
                for row in cursor.fetchall():
                    student_id, first_name, last_name, average = row
                    grade = self.calculate_grade(int(average), form_level)
                    
                    performers.append({
                        'name': f"{first_name} {last_name}",
                        'average': average,
                        'grade': grade,
                        'excellence_area': category.title()
                    })
                
                return performers
                
        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return []
    
    def get_subject_teachers(self, form_level: int = None, school_id: int = None) -> Dict[str, str]:
        """Get subject teachers for specific form level and school"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if form_level and school_id:
                    cursor.execute("SELECT subject, teacher_name FROM subject_teachers WHERE form_level = ? AND school_id = ?", (form_level, school_id))
                elif form_level:
                    cursor.execute("SELECT subject, teacher_name FROM subject_teachers WHERE form_level = ?", (form_level,))
                elif school_id:
                    cursor.execute("SELECT subject, teacher_name FROM subject_teachers WHERE school_id = ?", (school_id,))
                else:
                    cursor.execute("SELECT subject, teacher_name FROM subject_teachers")
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            self.logger.error(f"Error getting subject teachers: {e}")
            return {}
    
    def update_subject_teacher(self, subject: str, form_level: int, teacher_name: str, school_id: int = None):
        """Update teacher for a subject in specific form and school"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO subject_teachers (subject, form_level, teacher_name, updated_date, school_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (subject, form_level, teacher_name, datetime.now().isoformat(), school_id))
                self.logger.info(f"Updated teacher for {subject} Form {form_level}: {teacher_name}")
        except Exception as e:
            self.logger.error(f"Error updating subject teacher: {e}")
            raise
    
    def get_subject_position(self, student_id: int, subject: str, term: str, academic_year: str, form_level: int, school_id: int = None) -> str:
        """Get student position in a specific subject within their form (format: position/total)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("""
                        SELECT s.student_id, sm.mark
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.subject = ? AND sm.term = ? AND sm.academic_year = ? AND s.school_id = ?
                        ORDER BY sm.mark DESC
                    """, (form_level, subject, term, academic_year, school_id))
                else:
                    cursor.execute("""
                        SELECT s.student_id, sm.mark
                        FROM students s
                        JOIN student_marks sm ON s.student_id = sm.student_id
                        WHERE s.grade_level = ? AND sm.subject = ? AND sm.term = ? AND sm.academic_year = ?
                        ORDER BY sm.mark DESC
                    """, (form_level, subject, term, academic_year))
                
                rankings = cursor.fetchall()
                total_students = len(rankings)
                
                for i, (sid, mark) in enumerate(rankings):
                    if sid == student_id:
                        return f"{i + 1}/{total_students}"
                return f"0/{total_students}"
        except Exception as e:
            self.logger.error(f"Error getting subject position: {e}")
            return "0/0"
    
    def get_teacher_comment(self, grade: str) -> str:
        """Get teacher comment based on grade for Forms 3&4"""
        grade_comments = {
            '1': 'Distinction',
            '2': 'Distinction', 
            '3': 'Strong Credit',
            '4': 'Credit',
            '5': 'Credit',
            '6': 'Credit',
            '7': 'Pass',
            '8': 'Mere Pass',
            '9': 'Fail',
            'A': 'Excellent',
            'B': 'Very Good',
            'C': 'Good', 
            'D': 'Average',
            'F': 'Fail'
        }
        return grade_comments.get(grade, 'Needs Improvement')
    
    def update_school_settings(self, school_id: int, settings_data: Dict):
        """Update school settings in database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO school_settings 
                    (school_name, school_address, school_phone, school_email, 
                     pta_fund, next_term_begins, boys_uniform, girls_uniform, updated_date, school_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    settings_data.get('school_name'),
                    settings_data.get('school_address'),
                    settings_data.get('school_phone'),
                    settings_data.get('school_email'),
                    settings_data.get('pta_fund'),
                    settings_data.get('next_term_begins'),
                    settings_data.get('boys_uniform'),
                    settings_data.get('girls_uniform'),
                    datetime.now().isoformat(),
                    school_id
                ))
                
                # Update fees if provided
                if any(key in settings_data for key in ['pta_fund', 'sdf_fund', 'boarding_fee']):
                    cursor.execute("""
                        INSERT OR REPLACE INTO school_fees 
                        (id, pta_fund, sdf_fund, boarding_fee, updated_date)
                        VALUES (1, ?, ?, ?, ?)
                    """, (
                        settings_data.get('pta_fund'),
                        settings_data.get('sdf_fund'),
                        settings_data.get('boarding_fee'),
                        datetime.now().isoformat()
                    ))
                
                self.logger.info("School settings updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating school settings: {e}")
            raise
    
    def get_school_fees(self) -> Dict:
        """Get school fee information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT pta_fund, sdf_fund, boarding_fee FROM school_fees ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    return {
                        'pta_fund': row[0],
                        'sdf_fund': row[1],
                        'boarding_fee': row[2]
                    }
                else:
                    return {
                        'pta_fund': 'MK 50,000',
                        'sdf_fund': 'MK 30,000',
                        'boarding_fee': 'MK 150,000'
                    }
        except Exception as e:
            self.logger.error(f"Error getting school fees: {e}")
            return {
                'pta_fund': 'MK 50,000',
                'sdf_fund': 'MK 30,000',
                'boarding_fee': 'MK 150,000'
            }
    
    def delete_student_marks(self, student_id: int, school_id: int = None):
        """Delete all marks for a student"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("DELETE FROM student_marks WHERE student_id = ? AND school_id = ?", (student_id, school_id))
                else:
                    cursor.execute("DELETE FROM student_marks WHERE student_id = ?", (student_id,))
                self.logger.info(f"Deleted all marks for student {student_id}")
        except Exception as e:
            self.logger.error(f"Error deleting student marks: {e}")
            raise
    
    def delete_student(self, student_id: int, school_id: int = None):
        """Delete a student record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if school_id:
                    cursor.execute("DELETE FROM students WHERE student_id = ? AND school_id = ?", (student_id, school_id))
                else:
                    cursor.execute("DELETE FROM students WHERE student_id = ?",(student_id,))
                self.logger.info(f"Deleted student {student_id}")
        except Exception as e:
            self.logger.error(f"Error deleting student: {e}")
            raise
    
    def authenticate_school(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate school login"""
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT school_id, school_name, username, status, subscription_status, days_remaining
                    FROM schools 
                    WHERE username = ? AND password_hash = ? AND status = 'active'
                """, (username, password_hash))
                
                row = cursor.fetchone()
                if row:
                    # Update last login
                    cursor.execute("""
                        UPDATE schools SET last_login = ? WHERE school_id = ?
                    """, (datetime.now().isoformat(), row[0]))
                    
                    return {
                        'school_id': row[0],
                        'school_name': row[1],
                        'username': row[2],
                        'status': row[3],
                        'subscription_status': row[4],
                        'days_remaining': row[5]
                    }
                return None
        except Exception as e:
            self.logger.error(f"Error authenticating school: {e}")
            return None
    
    def add_school(self, school_data: Dict) -> int:
        """Add new school (Developer only)"""
        try:
            import hashlib
            from datetime import datetime, timedelta
            password_hash = hashlib.sha256(school_data['password'].encode()).hexdigest()
            
            # Set trial period (90 days)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=90)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if subscription columns exist, if not add them
                cursor.execute("PRAGMA table_info(schools)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'subscription_status' in columns:
                    cursor.execute("""
                        INSERT INTO schools (school_name, username, password_hash, subscription_status, 
                                           subscription_start_date, subscription_end_date, days_remaining)
                        VALUES (?, ?, ?, 'trial', ?, ?, 90)
                    """, (school_data['school_name'], school_data['username'], password_hash, 
                          start_date.isoformat(), end_date.isoformat()))
                else:
                    cursor.execute("""
                        INSERT INTO schools (school_name, username, password_hash)
                        VALUES (?, ?, ?)
                    """, (school_data['school_name'], school_data['username'], password_hash))
                
                school_id = cursor.lastrowid
                self.logger.info(f"Added school: {school_data['school_name']} (ID: {school_id})")
                return school_id
        except Exception as e:
            self.logger.error(f"Error adding school: {e}")
            raise
    
    def get_all_schools(self) -> List[Dict]:
        """Get all schools (Developer only)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT school_id, school_name, username, status, subscription_status, 
                           subscription_end_date, days_remaining, created_date, last_login
                    FROM schools ORDER BY school_name
                """)
                
                schools = []
                for row in cursor.fetchall():
                    schools.append({
                        'school_id': row[0],
                        'school_name': row[1],
                        'username': row[2],
                        'status': row[3],
                        'subscription_status': row[4],
                        'subscription_end_date': row[5],
                        'days_remaining': row[6],
                        'created_date': row[7],
                        'last_login': row[8]
                    })
                return schools
        except Exception as e:
            self.logger.error(f"Error getting schools: {e}")
            return []
    
    def update_school_status(self, school_id: int, status: str):
        """Update school status (Developer only)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schools SET status = ? WHERE school_id = ?
                """, (status, school_id))
                self.logger.info(f"Updated school {school_id} status to {status}")
        except Exception as e:
            self.logger.error(f"Error updating school status: {e}")
            raise
    
    def grant_subscription(self, school_id: int, months: int = 12):
        """Grant subscription to school (Developer only)"""
        try:
            from datetime import datetime, timedelta
            start_date = datetime.now()
            end_date = start_date + timedelta(days=months * 30)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schools 
                    SET subscription_status = 'paid', 
                        subscription_start_date = ?, 
                        subscription_end_date = ?,
                        days_remaining = ?
                    WHERE school_id = ?
                """, (start_date.isoformat(), end_date.isoformat(), months * 30, school_id))
                
                self.logger.info(f"Granted {months} months subscription to school {school_id}")
        except Exception as e:
            self.logger.error(f"Error granting subscription: {e}")
            raise
    
    def send_subscription_reminder(self, school_id: int = None):
        """Send subscription reminder to schools"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if school_id:
                    schools_query = "SELECT school_id, school_name, days_remaining FROM schools WHERE school_id = ?"
                    cursor.execute(schools_query, (school_id,))
                else:
                    schools_query = "SELECT school_id, school_name, days_remaining FROM schools WHERE subscription_status = 'trial' OR days_remaining <= 30"
                    cursor.execute(schools_query)
                
                schools = cursor.fetchall()
                
                for school_id, school_name, days_remaining in schools:
                    message = f"Dear {school_name}, your subscription expires in {days_remaining} days. Please renew to continue using the system."
                    
                    cursor.execute("""
                        INSERT INTO subscription_notifications (school_id, message, notification_type)
                        VALUES (?, ?, 'reminder')
                    """, (school_id, message))
                
                self.logger.info(f"Sent subscription reminders to {len(schools)} schools")
                return len(schools)
        except Exception as e:
            self.logger.error(f"Error sending subscription reminders: {e}")
            return 0
    
    def get_schools_to_lock(self) -> List[Dict]:
        """Get schools that should be locked for non-payment"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT school_id, school_name, username, days_remaining, subscription_end_date
                    FROM schools 
                    WHERE days_remaining <= 0 AND status = 'active'
                    ORDER BY school_name
                """)
                
                schools = []
                for row in cursor.fetchall():
                    schools.append({
                        'school_id': row[0],
                        'school_name': row[1],
                        'username': row[2],
                        'days_remaining': row[3],
                        'subscription_end_date': row[4]
                    })
                return schools
        except Exception as e:
            self.logger.error(f"Error getting schools to lock: {e}")
            return []
    
    def update_days_remaining(self):
        """Update days remaining for all schools"""
        try:
            from datetime import datetime
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT school_id, subscription_end_date FROM schools 
                    WHERE subscription_end_date IS NOT NULL
                """)
                
                schools = cursor.fetchall()
                for school_id, end_date_str in schools:
                    try:
                        end_date = datetime.fromisoformat(end_date_str)
                        days_remaining = (end_date - datetime.now()).days
                        
                        cursor.execute("""
                            UPDATE schools SET days_remaining = ? WHERE school_id = ?
                        """, (max(0, days_remaining), school_id))
                    except:
                        continue
                
                self.logger.info(f"Updated days remaining for {len(schools)} schools")
        except Exception as e:
            self.logger.error(f"Error updating days remaining: {e}")


def main():
    """Main function for testing the database operations"""
    print("School Reporting Database System")
    print("=" * 50)
    print("Features:")
    print("- Official Report Cards (Tests, Exams only)")
    print("- Internal Tracking (Quiz, Homework, Projects, etc.)")
    print("- Comprehensive Teacher Reports")
    print("=" * 50)
    
    # Initialize database
    db = SchoolDatabase()
    
    # Display assessment types
    print("\n📊 REPORT CARD Assessment Types:")
    report_types = db.get_report_card_assessment_types()
    for rt in report_types:
        print(f"  • {rt['type_name']}: {rt['description']}")
    
    print("\n📋 INTERNAL TRACKING Assessment Types:")
    internal_types = db.get_internal_tracking_assessment_types()
    for it in internal_types:
        print(f"  • {it['type_name']}: {it['description']}")
    
    print("\nDatabase system ready for use!")
    print("Use the methods to:")
    print("- generate_official_report_card() for student report cards")
    print("- generate_internal_tracking_report() for teacher tracking")
    print("- generate_comprehensive_teacher_report() for complete view")


if __name__ == "__main__":
    main()
