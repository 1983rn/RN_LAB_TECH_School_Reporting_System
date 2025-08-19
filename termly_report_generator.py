#!/usr/bin/env python3
"""
Termly Report Card Generator
Generates official school report cards showing only end-of-term exam marks
with teacher names for Forms 1-4 subjects and pass/fail determination
Pass Criteria: Must pass at least 6 subjects including English
Created: 2025-08-06
"""

from school_database import SchoolDatabase
from datetime import datetime
import json
import os

class TermlyReportGenerator:
    """Class for generating professional termly report cards with pass/fail determination"""
    
    def __init__(self, school_name="[SCHOOL NAME]", school_address="[SCHOOL ADDRESS]", school_phone="[PHONE]", school_email="[EMAIL]", pta_fee="[PTA FEE AMOUNT]", sdf_fee="[SDF FEE AMOUNT]", boarding_fee="[BOARDING FEE AMOUNT]", boys_uniform="[BOYS UNIFORM REQUIREMENTS]", girls_uniform="[GIRLS UNIFORM REQUIREMENTS]", emblem_path=None):
        self.db = SchoolDatabase()
        self.standard_subjects = [
            'Agriculture', 'Biology', 'Bible Knowledge', 'Chemistry', 
            'Chichewa', 'Computer Studies', 'English', 'Geography', 
            'History', 'Life Skills/SOS', 'Mathematics', 'Physics'
        ]
        # School information - editable fields
        self.school_name = school_name
        self.school_address = school_address
        self.school_phone = school_phone
        self.school_email = school_email
        # Fee information - editable fields
        self.pta_fee = pta_fee
        self.sdf_fee = sdf_fee
        self.boarding_fee = boarding_fee
        # Uniform requirements - editable fields
        self.boys_uniform = boys_uniform
        self.girls_uniform = girls_uniform
        # Malawi Government emblem image path
        self.emblem_path = emblem_path
    
    def generate_termly_report_card(self, student_id: int, term: str, academic_year: str = '2024-2025'):
        """Generate a complete termly report card with pass/fail status"""
        try:
            report_data = self.db.generate_termly_report_card(student_id, term, academic_year)
            return self.format_report_card(report_data)
        except Exception as e:
            print(f"Error generating report card: {e}")
            return None
    
    def generate_progress_report(self, student_id: int, term: str, academic_year: str = '2024-2025'):
        """Generate progress report using student marks from database"""
        try:
            # Get student info
            student = self.db.get_student_by_id(student_id)
            if not student:
                return None
            
            # Get student marks
            marks = self.db.get_student_marks(student_id, term, academic_year)
            if not marks:
                return None
            
            # Get position and points
            position_data = self.db.get_student_position_and_points(student_id, term, academic_year, student['grade_level'])
            
            return self.format_progress_report(student, marks, position_data, term, academic_year)
            
        except Exception as e:
            print(f"Error generating progress report: {e}")
            return None
    
    def format_report_card(self, report_data: dict) -> str:
        """Format the report card for display/printing with pass/fail information"""
        if not report_data:
            return "No report data available"
        
        student = report_data['student_info']
        grades = report_data['subject_grades']
        attendance = report_data['attendance_summary']
        stats = report_data['overall_statistics']
        
        # Official Malawi Government Header
        report = f"""
{'='*90}
                            REPUBLIC OF MALAWI
                         MINISTRY OF EDUCATION
                      
                    [🇲🇼 MALAWI GOVERNMENT EMBLEM 🇲🇼]
                         UNITY - WORK - PROGRESS
                        
{'='*90}

                        OFFICIAL SCHOOL REPORT CARD

{'-'*90}
SCHOOL INFORMATION:
{'-'*90}
School Name: {self.school_name}
Address: {self.school_address}
Telephone: {self.school_phone}
Email: {self.school_email}

{'='*90}
STUDENT INFORMATION:
{'='*90}
Student Number: {student['student_number']}
Full Name: {student['first_name']} {student['last_name']}
Form/Class: Form {student['grade_level']}
Academic Year: {report_data['academic_year']}
Term: {report_data['term']}
Report Generated: {datetime.now().strftime('%d/%m/%Y at %H:%M')}

{'='*90}
ACADEMIC PERFORMANCE - END OF TERM EXAMINATIONS
{'='*90}

{'Subject':<22} {'Mark':<8} {'Grade':<6} {'Status':<6} {'Subject Teacher':<30}
{'-'*90}
"""
        
        # Subject grades in the specified order
        for subject_name in self.standard_subjects:
            subject_found = False
            for grade in grades:
                if grade['subject_name'] == subject_name:
                    status = 'PASS' if grade['percentage'] >= 50 else 'FAIL'
                    # Highlight English specially
                    subject_display = f"{subject_name}*" if subject_name == 'English' else subject_name
                    report += f"{subject_display:<20} {grade['percentage']:>5.1f}% {grade['letter_grade']:<6} {status:<6} {grade['teacher_name']:<25}\n"
                    subject_found = True
                    break
            
            if not subject_found:
                subject_display = f"{subject_name}*" if subject_name == 'English' else subject_name
                report += f"{subject_display:<20} {'--':<6} {'--':<6} {'--':<6} {'Not Assigned':<25}\n"
        
        # Pass/Fail determination section
        report += f"""
{'-'*80}
OVERALL PERFORMANCE SUMMARY:
{'-'*80}

Total Subjects Taken: {stats['total_subjects']}
Subjects Passed (≥50%): {stats['passed_subjects']}
Overall Average: {stats['overall_average']}%
Overall Grade: {stats['overall_grade']}

English Performance: {stats['english_percentage']}% ({'PASS' if stats['english_passed'] else 'FAIL'})

{'='*80}
FINAL DETERMINATION: {stats['overall_status']}
{'='*80}

Reason: {stats['status_reason']}

PASS CRITERIA:
- Must pass at least 6 subjects (including English*)
- English* is mandatory for overall pass
- Subject pass mark: 50%

* English is a compulsory subject for promotion

"""
        
        # Attendance summary
        if attendance:
            total_days = attendance.get('total_days', 0)
            present_days = attendance.get('present_days', 0)
            absent_days = attendance.get('absent_days', 0)
            late_days = attendance.get('late_days', 0)
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            report += f"""
{'='*80}
ATTENDANCE SUMMARY - {report_data['term'].upper()}
{'='*80}

Total School Days: {total_days}
Days Present: {present_days}
Days Absent: {absent_days}
Days Late: {late_days}
Attendance Rate: {attendance_percentage:.1f}%

"""
        
        # Performance analysis
        if stats['overall_status'] == 'PASS':
            report += f"""
{'='*80}
PERFORMANCE ANALYSIS:
{'='*80}

✅ CONGRATULATIONS! You have met the promotion criteria.

Strengths:
- Passed {stats['passed_subjects']} out of {stats['total_subjects']} subjects
- Successfully passed English (mandatory requirement)
- Overall average of {stats['overall_average']}%

"""
        else:
            report += f"""
{'='*80}
PERFORMANCE ANALYSIS:
{'='*80}

⚠️  ATTENTION REQUIRED: You have not met the promotion criteria.

Areas for Improvement:
"""
            if not stats['english_passed']:
                report += f"- English: {stats['english_percentage']}% (MUST PASS - Compulsory subject)\n"
            
            if stats['passed_subjects'] < 6:
                needed = 6 - stats['passed_subjects']
                report += f"- Need to pass {needed} more subject(s) to meet minimum requirement\n"
                report += f"- Currently passed only {stats['passed_subjects']} out of {stats['total_subjects']} subjects\n"
            
            report += f"\nRemedial Action Required:\n"
            report += f"- Focus on improving failed subjects\n"
            if not stats['english_passed']:
                report += f"- Priority: English (mandatory for promotion)\n"
            report += f"- Seek additional support from teachers\n"
            report += f"- Consider supplementary examinations where available\n\n"
        
        # Comments section
        report += f"""
{'='*80}
SUBJECT TEACHER COMMENTS:
{'='*80}

"""
        
        # Add any subject-specific comments
        comment_added = False
        for grade in grades:
            if grade.get('comments'):
                report += f"{grade['subject_name']}: {grade['comments']}\n"
                comment_added = True
        
        if not comment_added:
            report += "No specific subject comments recorded.\n\n"
        
        # Footer with fees and uniform information
        receipt_number = datetime.now().strftime('%Y%m%d%H%M%S')
        receipt_datetime = datetime.now().strftime('%d/%m/%Y at %H:%M:%S')
        
        report += f"""
{'='*90}
NEXT TERM BEGINS: ________________    CURRENT FEE BALANCE: ________________

{'='*90}
EXPECTED FEES FOR NEXT TERM:
{'='*90}
PTA Fee: {self.pta_fee}
SDF (School Development Fund): {self.sdf_fee}
Boarding Fee: {self.boarding_fee}

{'='*90}
SCHOOL UNIFORM REQUIREMENTS:
{'='*90}
BOYS UNIFORM:
{self.boys_uniform}

GIRLS UNIFORM:
{self.girls_uniform}

{'='*90}
OFFICIAL SIGNATURES:
{'='*90}
CLASS TEACHER: _________________________    DATE: _______________

HEAD TEACHER: _________________________    DATE: _______________

{'='*90}
                    END OF OFFICIAL REPORT CARD
{'='*90}

{'-'*90}
Official Receipt Generated No: {receipt_number} ({receipt_datetime})
Created by: RN_LAB_TECH
{'-'*90}

"""
        return report
    
    def generate_pass_fail_summary(self, form_level: int, term: str, academic_year: str = '2024-2025'):
        """Generate a summary of pass/fail statistics for a class"""
        try:
            students = self.db.get_students_by_grade(form_level)
            summary_data = {
                'total_students': len(students),
                'passed_students': 0,
                'failed_students': 0,
                'failed_english_only': 0,
                'failed_insufficient_subjects': 0,
                'failed_both': 0,
                'student_details': []
            }
            
            print(f"📊 Analyzing pass/fail status for Form {form_level} - {term}...")
            
            for student in students:
                try:
                    report_data = self.db.generate_termly_report_card(
                        student['student_id'], term, academic_year
                    )
                    
                    if report_data:
                        stats = report_data['overall_statistics']
                        student_detail = {
                            'name': f"{student['first_name']} {student['last_name']}",
                            'student_number': student['student_number'],
                            'status': stats['overall_status'],
                            'passed_subjects': stats['passed_subjects'],
                            'english_passed': stats['english_passed'],
                            'english_percentage': stats['english_percentage'],
                            'overall_average': stats['overall_average']
                        }
                        
                        summary_data['student_details'].append(student_detail)
                        
                        if stats['overall_status'] == 'PASS':
                            summary_data['passed_students'] += 1
                        else:
                            summary_data['failed_students'] += 1
                            
                            # Categorize failure reasons
                            if stats['passed_subjects'] >= 6 and not stats['english_passed']:
                                summary_data['failed_english_only'] += 1
                            elif stats['passed_subjects'] < 6 and stats['english_passed']:
                                summary_data['failed_insufficient_subjects'] += 1
                            else:
                                summary_data['failed_both'] += 1
                
                except Exception as e:
                    print(f"Error processing {student['first_name']} {student['last_name']}: {e}")
            
            return self.format_class_summary(summary_data, form_level, term, academic_year)
            
        except Exception as e:
            print(f"Error generating class summary: {e}")
            return None
    
    def format_class_summary(self, summary_data: dict, form_level: int, term: str, academic_year: str) -> str:
        """Format the class pass/fail summary"""
        
        pass_rate = (summary_data['passed_students'] / summary_data['total_students'] * 100) if summary_data['total_students'] > 0 else 0
        
        report = f"""
{'='*80}
                    CLASS PASS/FAIL SUMMARY REPORT
{'='*80}

Class: Form {form_level}
Term: {term}
Academic Year: {academic_year}
Date Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}

{'='*80}
OVERALL STATISTICS:
{'='*80}

Total Students: {summary_data['total_students']}
Students Passed: {summary_data['passed_students']} ({pass_rate:.1f}%)
Students Failed: {summary_data['failed_students']} ({100-pass_rate:.1f}%)

{'='*80}
FAILURE ANALYSIS:
{'='*80}

Failed due to English only: {summary_data['failed_english_only']} students
(Passed 6+ subjects but failed English)

Failed due to insufficient subjects: {summary_data['failed_insufficient_subjects']} students
(Passed English but failed to pass 6 subjects)

Failed both criteria: {summary_data['failed_both']} students
(Failed English AND passed less than 6 subjects)

{'='*80}
INDIVIDUAL STUDENT RESULTS:
{'='*80}

{'Name':<25} {'Std.No':<10} {'Status':<6} {'Subjects':<8} {'English':<8} {'Average':<8}
{'-'*80}
"""
        
        # Sort students by status (pass first) then by name
        sorted_students = sorted(summary_data['student_details'], 
                               key=lambda x: (x['status'] == 'FAIL', x['name']))
        
        for student in sorted_students:
            english_status = f"{student['english_percentage']:.0f}%"
            report += f"{student['name'][:24]:<25} {student['student_number']:<10} {student['status']:<6} {student['passed_subjects']:<8} {english_status:<8} {student['overall_average']:.1f}%\n"
        
        # Recommendations
        report += f"""

{'='*80}
RECOMMENDATIONS:
{'='*80}

For Students Who Failed English:
- Organize remedial English classes
- Focus on basic English communication skills
- Consider individual tutoring for English
- English is mandatory - no promotion without pass

For Students With Insufficient Subjects:
- Identify weakest subjects for targeted support
- Group remedial classes for common weak subjects
- Extra practice sessions before next examinations
- Peer tutoring programs

For High Performing Students:
- Advanced enrichment programs
- Peer mentoring opportunities
- Leadership roles in study groups

{'='*80}
"""
        
        return report
    
    def format_progress_report(self, student, marks, position_data, term, academic_year):
        """Format progress report with official Malawi formatting"""
        form_level = student['grade_level']
        
        # Calculate statistics
        total_marks = sum(data['mark'] for data in marks.values())
        subject_count = len(marks)
        average = total_marks / subject_count if subject_count > 0 else 0
        
        # Count passed subjects
        passed_subjects = sum(1 for data in marks.values() if data['mark'] >= 50)
        english_passed = marks.get('English', {}).get('mark', 0) >= 50
        
        # Determine overall status
        overall_status = self.db.determine_pass_fail_status(passed_subjects, english_passed)
        
        # Calculate average grade for junior forms (after overall_status calculation)
        if form_level <= 2:
            grades = [marks[subject]['grade'] for subject in marks if subject in marks]
            if grades:
                # Count frequency of each grade
                grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
                for grade in grades:
                    if grade in grade_counts:
                        grade_counts[grade] += 1
                
                # Find most common grade(s)
                max_count = max(grade_counts.values())
                most_common_grades = [grade for grade, count in grade_counts.items() if count == max_count]
                
                if len(most_common_grades) == 1:
                    # Single most common grade
                    avg_grade = most_common_grades[0]
                else:
                    # Tie - use average marks to determine grade
                    total_marks = sum(marks[subject]['mark'] for subject in marks if subject in marks)
                    average_mark = total_marks / len(marks)
                    avg_grade = self.db.calculate_grade(int(average_mark), form_level)
                
                # If student has passed but average grade is F, find next possible pass grade
                if avg_grade == 'F' and overall_status == 'PASS':
                    # Get passing grades only (D, C, B, A)
                    passing_grades = [g for g in grades if g in ['A', 'B', 'C', 'D']]
                    if passing_grades:
                        # Count frequency of passing grades only
                        pass_grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
                        for grade in passing_grades:
                            pass_grade_counts[grade] += 1
                        
                        # Find most common passing grade
                        max_pass_count = max(pass_grade_counts.values())
                        most_common_pass_grades = [grade for grade, count in pass_grade_counts.items() if count == max_pass_count]
                        
                        if len(most_common_pass_grades) == 1:
                            avg_grade = most_common_pass_grades[0]
                        else:
                            # If tie among passing grades, use average marks to determine grade
                            total_marks = sum(marks[subject]['mark'] for subject in marks if subject in marks)
                            average_mark = total_marks / len(marks)
                            avg_grade = self.db.calculate_grade(int(average_mark), form_level)
            else:
                avg_grade = 'F'
        
        # Get school settings
        settings = self.db.get_school_settings()
        school_name = settings.get('school_name', self.school_name)
        school_address = settings.get('school_address', self.school_address)
        
        # Get subject teachers for this form level
        subject_teachers = self.db.get_subject_teachers(form_level)
        
        # Format term display
        term_display = f"Term: {term.replace('Term', '').strip()}"
        
        # Format school address - center each line properly
        address_parts = ['PRIVATE BAG 211', 'KAWALE', 'LILONGWE', 'MALAWI']
        centered_address = '\n'.join([f"{' ' * ((80 - len(part)) // 2)}{part}" for part in address_parts])
        
        # Address is already properly centered for all forms
        
        report = f"""
{'=' * 80}
{' ' * ((80 - len(school_name)) // 2)}**{school_name}**

{centered_address}

{' ' * ((80 - len('**PROGRESS REPORT**')) // 2)}**PROGRESS REPORT**
{'=' * 80}

Serial No:        {student['student_number']}
Student Name:     {student['first_name']} {student['last_name']}
{term_display.replace('Term:', 'Term:            ')}
Form:             {form_level}
Year:             {academic_year}
Position:         {position_data['position']}/{position_data['total_students']}                    {'Average Grade: ' + avg_grade if form_level <= 2 else 'Aggregate Points: ' + str(position_data['aggregate_points'])}

Subject                Marks Grade Pos  Comment      Signature
================================================================================
"""
        
        # Add subjects in order
        for subject in self.standard_subjects:
            if subject in marks:
                mark = marks[subject]['mark']
                grade = marks[subject]['grade']
                position = self.db.get_subject_position(student['student_id'], subject, term, academic_year, form_level)
                comment = self.db.get_teacher_comment(grade)
                teacher = subject_teachers.get(subject, f"{subject} Teacher F{form_level}")
                report += f"{subject:<20} {mark:>3} {grade:>5} {position:>5} {comment:<12} {teacher[:10]:<10}\n"
            else:
                report += f"{subject:<20} {'--':>3} {'--':>5} {'--':>5} {'Not taken':<12} {'--':<10}\n"
        
        # Add aggregate points for best 6 subjects (Forms 3&4)
        if form_level >= 3:
            best_marks = sorted([data['mark'] for data in marks.values()], reverse=True)[:6]
            grade_points = []
            for mark in best_marks:
                grade = self.db.calculate_grade(mark, form_level)
                grade_points.append(int(grade) if grade.isdigit() else 9)
            aggregate_points = sum(grade_points)
            report += f"\n================================================================================\n\n**Aggregate Points (Best Six): {aggregate_points}**\n"
        
        # Add grading system
        if form_level <= 2:
            report += f"\nGRADING: A(80-100) B(70-79) C(60-69) D(50-59) F(0-49)\n"
        else:
            report += f"\nMSCE GRADING: 1(75-100) 2(70-74) 3(65-69) 4(60-64) 5(55-59) 6(50-54) 7(45-49) 8(40-44) 9(0-39)\n"
        
        # Auto-generated comments with pass/fail status
        if overall_status == 'PASS':
            form_teacher_comment = f"PASSED - Excellent performance! Passed {passed_subjects} subjects with {average:.1f}% average."
            head_teacher_comment = "PASSED - Well done. Keep up the good work."
        else:
            form_teacher_comment = f"FAILED - Needs improvement. Focus on weak subjects, especially English."
            head_teacher_comment = "FAILED - Extra effort required. Seek help from teachers."
        
        # Get fee information
        fee_info = self.db.get_school_fees()
        
        report += f"""
FORM TEACHER: {form_teacher_comment}
HEAD TEACHER: {head_teacher_comment}

CLASS TEACHER SIGN: ________________________

================================================================================
NEXT TERM: {settings.get('next_term_begins', 'TBA')}
FEES - PTA: {fee_info.get('pta_fund', 'MK 50,000')} | SDF: {fee_info.get('sdf_fund', 'MK 30,000')} | Boarding: {fee_info.get('boarding_fee', 'MK 150,000')}
UNIFORM - Girls: {settings.get('girls_uniform', 'White blouse, black skirt, black shoes')}
Boys: {settings.get('boys_uniform', 'White shirt, black trousers, black shoes')}
================================================================================

{' ' * ((80 - len('Generated by: RN_LAB_TECH')) // 2)}Generated by: RN_LAB_TECH
{' ' * ((80 - len(f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}')) // 2)}Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        
        return report
    
    def export_progress_report(self, student_id: int, term: str, academic_year: str = '2024-2025'):
        """Export progress report to PDF file"""
        student = self.db.get_student_by_id(student_id)
        if not student:
            return None
            
        student_name = f"{student['first_name']}_{student['last_name']}"
        filename = f"{student_name}_{term}_Progress_Report_{academic_year.replace('-', '_')}.pdf"
        
        report = self.generate_progress_report(student_id, term, academic_year)
        
        if report:
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageTemplate, Frame
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
                from reportlab.lib import colors
                from reportlab.platypus.doctemplate import BaseDocTemplate
                
                # Create custom document with colorful border
                class BorderedDocTemplate(BaseDocTemplate):
                    def __init__(self, filename, **kwargs):
                        BaseDocTemplate.__init__(self, filename, **kwargs)
                        
                    def draw_border(self, canvas, doc):
                        # Draw colorful border
                        canvas.saveState()
                        
                        # Outer border - Blue
                        canvas.setStrokeColor(colors.blue)
                        canvas.setLineWidth(4)
                        canvas.rect(20, 20, A4[0]-40, A4[1]-40)
                        
                        # Middle border - Green
                        canvas.setStrokeColor(colors.green)
                        canvas.setLineWidth(2)
                        canvas.rect(30, 30, A4[0]-60, A4[1]-60)
                        
                        # Inner border - Red
                        canvas.setStrokeColor(colors.red)
                        canvas.setLineWidth(1)
                        canvas.rect(40, 40, A4[0]-80, A4[1]-80)
                        
                        canvas.restoreState()
                
                doc = BorderedDocTemplate(filename, pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch, leftMargin=0.8*inch, rightMargin=0.8*inch)
                
                # Create frame and page template with border
                frame = Frame(0.8*inch, 0.8*inch, A4[0]-1.6*inch, A4[1]-1.6*inch, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
                template = PageTemplate(id='bordered', frames=frame, onPage=doc.draw_border)
                doc.addPageTemplates([template])
                styles = getSampleStyleSheet()
                story = []
                
                # Get school settings and student info for PDF processing
                settings = self.db.get_school_settings()
                school_name = settings.get('school_name', 'DEMO SECONDARY SCHOOL')
                student_info = self.db.get_student_by_id(student_id)
                form_level = student_info['grade_level'] if student_info else 1
                
                # Add logo if exists - smaller for A4 fit
                logo_path = "Malawi Government logo.png"
                if os.path.exists(logo_path):
                    try:
                        logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                        story.append(logo)
                        story.append(Spacer(1, 6))
                    except:
                        pass
                
                # Create styles with black text and background colors only
                school_name_style = ParagraphStyle('SchoolName', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black)
                address_style = ParagraphStyle('Address', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black)
                progress_style = ParagraphStyle('Progress', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black)
                normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, fontName='Helvetica', textColor=colors.black)
                section_style = ParagraphStyle('Section', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.black)
                
                # Add school header with reduced spacing for Forms 3-4
                spacing = 3 if form_level >= 3 else 6
                story.append(Paragraph(f"<b>{school_name}</b>", school_name_style))
                story.append(Spacer(1, spacing))
                
                # Add centered address
                story.append(Paragraph(f"<b>PRIVATE BAG 211</b>", address_style))
                story.append(Paragraph(f"<b>KAWALE</b>", address_style))
                story.append(Paragraph(f"<b>LILONGWE</b>", address_style))
                story.append(Paragraph(f"<b>MALAWI</b>", address_style))
                story.append(Spacer(1, spacing*2))
                
                # Add progress report title
                story.append(Paragraph(f"<b>PROGRESS REPORT</b>", progress_style))
                story.append(Spacer(1, spacing*2))
                

                
                # Build table data directly from marks data
                marks = self.db.get_student_marks(student_id, term, academic_year)
                subject_teachers = self.db.get_subject_teachers(form_level)
                
                # Create table with actual data
                table_data = [['Subject', 'Marks', 'Grade', 'Position', 'Teachers Comment', 'Signature']]
                
                for subject in self.standard_subjects:
                    if subject in marks:
                        mark = marks[subject]['mark']
                        grade = marks[subject]['grade']
                        position = self.db.get_subject_position(student_id, subject, term, academic_year, form_level)
                        comment = self.db.get_teacher_comment(grade)
                        teacher = subject_teachers.get(subject, f"{subject} Teacher F{form_level}")
                        table_data.append([subject, str(mark), grade, str(position), comment, teacher[:15]])
                    else:
                        table_data.append([subject, '--', '--', '--', 'Not taken', '--'])
                
                # Create professional table
                table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.5*inch, 1.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                
                # Add student information with uniform spacing using table
                student_data = [
                    ['Serial No:', student_info['student_number']],
                    ['Student Name:', f"{student_info['first_name']} {student_info['last_name']}"],
                    ['Term:', term.replace('Term', '').strip()],
                    ['Form:', str(form_level)],
                    ['Year:', academic_year]
                ]
                
                student_table = Table(student_data, colWidths=[1.5*inch, 4*inch])
                student_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                story.append(student_table)
                
                # Get position data for PDF
                position_data = self.db.get_student_position_and_points(student_id, term, academic_year, form_level)
                if form_level <= 2:
                    # Calculate average grade for junior forms
                    marks = self.db.get_student_marks(student_id, term, academic_year)
                    passed_subjects = sum(1 for data in marks.values() if data['mark'] >= 50)
                    english_passed = marks.get('English', {}).get('mark', 0) >= 50
                    overall_status = self.db.determine_pass_fail_status(passed_subjects, english_passed)
                    
                    grades = [marks[subject]['grade'] for subject in marks if subject in marks]
                    if grades:
                        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
                        for grade in grades:
                            if grade in grade_counts:
                                grade_counts[grade] += 1
                        
                        max_count = max(grade_counts.values())
                        most_common_grades = [grade for grade, count in grade_counts.items() if count == max_count]
                        
                        if len(most_common_grades) == 1:
                            avg_grade = most_common_grades[0]
                        else:
                            total_marks = sum(marks[subject]['mark'] for subject in marks if subject in marks)
                            average_mark = total_marks / len(marks)
                            avg_grade = self.db.calculate_grade(int(average_mark), form_level)
                        
                        if avg_grade == 'F' and overall_status == 'PASS':
                            passing_grades = [g for g in grades if g in ['A', 'B', 'C', 'D']]
                            if passing_grades:
                                pass_grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
                                for grade in passing_grades:
                                    pass_grade_counts[grade] += 1
                                
                                max_pass_count = max(pass_grade_counts.values())
                                most_common_pass_grades = [grade for grade, count in pass_grade_counts.items() if count == max_pass_count]
                                
                                if len(most_common_pass_grades) == 1:
                                    avg_grade = most_common_pass_grades[0]
                                else:
                                    total_marks = sum(marks[subject]['mark'] for subject in marks if subject in marks)
                                    average_mark = total_marks / len(marks)
                                    avg_grade = self.db.calculate_grade(int(average_mark), form_level)
                    else:
                        avg_grade = 'F'
                    
                    position_info = f"{position_data['position']}/{position_data['total_students']}                    Average Grade: {avg_grade}"
                else:
                    position_info = f"{position_data['position']}/{position_data['total_students']}                    Aggregate Points: {position_data['aggregate_points']}"
                
                # Add position as separate table row
                position_table = Table([['Position:', position_info]], colWidths=[1.5*inch, 4*inch])
                position_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                story.append(position_table)
                
                story.append(Spacer(1, 6 if form_level >= 3 else 12))
                
                # Add the table
                story.append(table)
                
                # Add aggregate points for senior forms (left-aligned below table)
                if form_level >= 3:
                    story.append(Spacer(1, 3))
                    story.append(Paragraph(f"<b>**Aggregate Points (Best Six): {position_data['aggregate_points']}**</b>", ParagraphStyle('AggregatePoints', parent=styles['Normal'], fontSize=10, alignment=TA_LEFT, fontName='Helvetica-Bold', textColor=colors.black)))
                
                story.append(Spacer(1, 6 if form_level >= 3 else 12))
                
                # Define style and spacing for footer based on form level
                if form_level <= 2:
                    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.black, leading=10)
                    grading_style = footer_style
                    spacer_size = 6
                    teacher_comment_spacer = 4
                else:
                    # Slightly increase footer for Forms 3 and 4 to use more space
                    footer_style = ParagraphStyle('FooterStyleSqueezed', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.black, leading=10)
                    grading_style = ParagraphStyle('GradingSqueezed', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.black, leading=10)
                    spacer_size = 6
                    teacher_comment_spacer = 4

                # Add grading system
                if form_level <= 2:
                    story.append(Paragraph(f"<b><u>GRADING:</u> A(80-100) B(70-79) C(60-69) D(50-59) F(0-49)</b>", grading_style))
                else:
                    story.append(Paragraph(f"<b><u>MSCE GRADING:</u> 1(75-100) 2(70-74) 3(65-69) 4(60-64) 5(55-59) 6(50-54) 7(45-49) 8(40-44) 9(0-39)</b>", grading_style))
                story.append(Spacer(1, spacer_size))
                
                # Add teacher comments
                marks = self.db.get_student_marks(student_id, term, academic_year)
                passed_subjects = sum(1 for data in marks.values() if data['mark'] >= 50)
                english_passed = marks.get('English', {}).get('mark', 0) >= 50
                overall_status = self.db.determine_pass_fail_status(passed_subjects, english_passed)
                average = sum(data['mark'] for data in marks.values()) / len(marks) if marks else 0
                
                if overall_status == 'PASS':
                    form_teacher_comment = f"PASSED - Excellent performance! Passed {passed_subjects} subjects with {average:.1f}% average."
                    head_teacher_comment = "PASSED - Well done. Keep up the good work."
                else:
                    form_teacher_comment = f"FAILED - Needs improvement. Focus on weak subjects, especially English."
                    head_teacher_comment = "FAILED - Extra effort required. Seek help from teachers."
                
                story.append(Paragraph(f"<b><u>FORM TEACHER:</u> {form_teacher_comment}</b>", footer_style))
                story.append(Paragraph(f"<b><u>HEAD TEACHER:</u> {head_teacher_comment}</b>", footer_style))
                story.append(Spacer(1, teacher_comment_spacer))
                story.append(Paragraph(f"<b><u>CLASS TEACHER SIGN:</u> ________________________</b>", footer_style))
                story.append(Spacer(1, spacer_size))
                
                # Add fees and uniform information
                settings = self.db.get_school_settings()
                fee_info = self.db.get_school_fees()
                
                story.append(Paragraph(f"<b><u>NEXT TERM BEGINS ON:</u> {settings.get('next_term_begins', '16 September, 2025')}</b>", footer_style))
                story.append(Paragraph(f"<b><u>FEES</u> - <u>PTA:</u> {fee_info.get('pta_fund', 'MK 45,000')} | <u>SDF:</u> {fee_info.get('sdf_fund', 'MK 5,000')} | <u>Boarding:</u> {fee_info.get('boarding_fee', '')}</b>", footer_style))
                story.append(Paragraph(f"<b><u>UNIFORM</u> - <u>Girls:</u> {settings.get('girls_uniform', 'White blouse, black skirt, black shoes')}</b>", footer_style))
                story.append(Paragraph(f"<b><u>Boys:</u> {settings.get('boys_uniform', 'White shirt, black trousers, black shoes')}</b>", footer_style))
                story.append(Spacer(1, spacer_size))
                
                # Add footer with centered text
                # Squeeze the final footer for Forms 3 and 4
                if form_level <= 2:
                    story.append(Paragraph(f"<b>Generated by: RN_LAB_TECH</b>", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black)))
                    story.append(Paragraph(f"<b>Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}</b>", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black)))
                else:
                    story.append(Paragraph(f"<b>Generated by: RN_LAB_TECH</b>", ParagraphStyle('FooterSqueezed', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black, leading=10)))
                    story.append(Paragraph(f"<b>Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}</b>", ParagraphStyle('FooterSqueezed', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.black, leading=10)))
                
                doc.build(story)
                return filename
            except Exception as e:
                print(f"Error creating PDF: {e}")
                # Fallback to text file
                filename = filename.replace('.pdf', '.txt')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                return filename
        return None
    
    def export_report_to_file(self, student_id: int, term: str, academic_year: str = '2024-2025', 
                             filename: str = None):
        """Export report card to text file"""
        if not filename:
            student = self.db.get_student_by_id(student_id)
            student_name = f"{student['first_name']}_{student['last_name']}" if student else f"student_{student_id}"
            filename = f"{student_name}_{term}_report_{academic_year.replace('-', '_')}.txt"
        
        report_card = self.generate_termly_report_card(student_id, term, academic_year)
        
        if report_card:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_card)
                print(f"✅ Report card exported to: {filename}")
                return filename
            except Exception as e:
                print(f"❌ Error exporting report: {e}")
                return None
        else:
            print("❌ No report data to export")
            return None
    
    def export_class_summary_to_file(self, form_level: int, term: str, academic_year: str = '2024-2025'):
        """Export class pass/fail summary to file"""
        filename = f"Form_{form_level}_{term}_PassFail_Summary_{academic_year.replace('-', '_')}.txt"
        
        summary = self.generate_pass_fail_summary(form_level, term, academic_year)
        
        if summary:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"✅ Class summary exported to: {filename}")
                return filename
            except Exception as e:
                print(f"❌ Error exporting summary: {e}")
                return None
        else:
            print("❌ No summary data to export")
            return None


def main():
    """Demo function showing the enhanced termly report generator"""
    print("📊 ENHANCED TERMLY REPORT CARD GENERATOR")
    print("=" * 60)
    print("🎯 PASS CRITERIA:")
    print("   • Must pass at least 6 subjects")
    print("   • English is MANDATORY (must pass)")
    print("   • Pass mark: 50%")
    print("=" * 60)
    
    generator = TermlyReportGenerator()
    
    print("\n📚 Standard Subjects on Report Card:")
    for i, subject in enumerate(generator.standard_subjects, 1):
        marker = " *MANDATORY*" if subject == "English" else ""
        print(f"  {i:2d}. {subject}{marker}")
    
    print("\n" + "=" * 60)
    print("💡 USAGE EXAMPLES:")
    print("=" * 60)
    
    print("\n1. Generate individual report with pass/fail:")
    print("   generator.generate_termly_report_card(student_id=1, term='Term 1')")
    
    print("\n2. Generate class pass/fail summary:")
    print("   generator.generate_pass_fail_summary(form_level=1, term='Term 1')")
    
    print("\n3. Export individual report:")
    print("   generator.export_report_to_file(student_id=1, term='Term 1')")
    
    print("\n4. Export class summary:")
    print("   generator.export_class_summary_to_file(form_level=1, term='Term 1')")
    
    print("\n📋 NEW FEATURES:")
    print("  • Pass/Fail determination based on school criteria")
    print("  • English mandatory requirement enforcement")
    print("  • Detailed performance analysis")
    print("  • Class-wide pass/fail statistics")
    print("  • Failure reason categorization")
    print("  • Remedial action recommendations")


if __name__ == "__main__":
    main()
