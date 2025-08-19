#!/usr/bin/env python3
"""
Performance Analyzer Module
Generates reports for best performing students by class, subject, and department
Departments: Sciences, Humanities, Languages
Created: 2025-08-06
"""

from school_database import SchoolDatabase
from datetime import datetime
import json
from typing import List, Dict, Optional

class PerformanceAnalyzer:
    """Class for analyzing and generating performance reports"""
    
    def __init__(self, school_name="[SCHOOL NAME]"):
        self.db = SchoolDatabase()
        self.school_name = school_name
        
        # Department classifications
        self.departments = {
            'Sciences': {
                'subjects': ['Agriculture', 'Biology', 'Chemistry', 'Physics', 'Mathematics', 'Computer Studies'],
                'description': 'Science and Mathematics Department'
            },
            'Humanities': {
                'subjects': ['Bible Knowledge', 'Geography', 'History', 'Life Skills/SOS'],
                'description': 'Humanities and Social Studies Department'
            },
            'Languages': {
                'subjects': ['English', 'Chichewa'],
                'description': 'Languages Department'
            }
        }
        
        self.all_subjects = [
            'Agriculture', 'Biology', 'Bible Knowledge', 'Chemistry', 
            'Chichewa', 'Computer Studies', 'English', 'Geography', 
            'History', 'Life Skills/SOS', 'Mathematics', 'Physics'
        ]
    
    def get_student_rankings(self, form_level: int, term: str, academic_year: str = '2024-2025') -> List[Dict]:
        """Get student rankings for a specific form level"""
        return self.db.get_student_rankings(form_level, term, academic_year)
    
    def get_top_performers(self, category: str, form_level: int, term: str, academic_year: str = '2024-2025') -> List[Dict]:
        """Get top performers by category"""
        return self.db.get_top_performers(category, form_level, term, academic_year)
    
    def get_best_performing_students_by_class(self, form_level: int, term: str, academic_year: str = '2024-2025', top_n: int = 10) -> Dict:
        """Generate best performing students report for a specific class"""
        try:
            rankings = self.db.get_student_rankings(form_level, term, academic_year)
            if not rankings:
                return None
                
            top_students = rankings[:top_n]
            
            return {
                'report_type': f'Best Performing Students - Form {form_level}',
                'form_level': form_level,
                'term': term,
                'academic_year': academic_year,
                'top_students': top_students,
                'generated_date': datetime.now().isoformat()
            }
                
        except Exception as e:
            print(f"Error generating class performance report: {e}")
            return None
    
    def get_best_performing_students_by_subject(self, subject_name: str, term: str, academic_year: str = '2024-2025', top_n: int = 10) -> Dict:
        """Generate best performing students report for a specific subject across all forms"""
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT 
                        s.student_id,
                        s.student_number,
                        s.first_name,
                        s.last_name,
                        s.grade_level,
                        sm.mark as percentage,
                        sm.grade as letter_grade
                    FROM students s
                    JOIN student_marks sm ON s.student_id = sm.student_id
                    WHERE sm.subject = ?
                    AND sm.term = ?
                    AND sm.academic_year = ?
                    AND s.status = 'Active'
                    ORDER BY sm.mark DESC
                    LIMIT ?
                """
                
                import pandas as pd
                df = pd.read_sql_query(query, conn, params=(subject_name, term, academic_year, top_n))
                
                return {
                    'report_type': f'Best Performing Students - {subject_name}',
                    'subject_name': subject_name,
                    'term': term,
                    'academic_year': academic_year,
                    'top_students': df.to_dict('records'),
                    'generated_date': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Error generating subject performance report: {e}")
            return None
    
    def get_best_performing_students_by_department(self, department_name: str, term: str, academic_year: str = '2024-2025', top_n: int = 10) -> Dict:
        """Generate best performing students report for a specific department"""
        try:
            if department_name not in self.departments:
                raise ValueError(f"Department '{department_name}' not found. Available departments: {list(self.departments.keys())}")
            
            department_subjects = self.departments[department_name]['subjects']
            subjects_placeholder = ','.join(['?' for _ in department_subjects])
            
            with self.db.get_connection() as conn:
                query = f"""
                    SELECT 
                        s.student_id,
                        s.student_number,
                        s.first_name,
                        s.last_name,
                        s.grade_level,
                        AVG(sm.mark) as department_average,
                        COUNT(sm.mark_id) as subjects_taken_in_dept,
                        SUM(CASE WHEN sm.mark >= 50 THEN 1 ELSE 0 END) as subjects_passed_in_dept,
                        MIN(sm.mark) as lowest_mark_in_dept,
                        MAX(sm.mark) as highest_mark_in_dept
                    FROM students s
                    JOIN student_marks sm ON s.student_id = sm.student_id
                    WHERE sm.subject IN ({subjects_placeholder})
                    AND sm.term = ?
                    AND sm.academic_year = ?
                    AND s.status = 'Active'
                    GROUP BY s.student_id
                    HAVING subjects_taken_in_dept >= 2
                    ORDER BY department_average DESC, subjects_passed_in_dept DESC
                    LIMIT ?
                """
                
                import pandas as pd
                params = department_subjects + [term, academic_year, top_n]
                df = pd.read_sql_query(query, conn, params=params)
                
                return {
                    'report_type': f'Best Performing Students - {department_name} Department',
                    'department_name': department_name,
                    'department_subjects': department_subjects,
                    'term': term,
                    'academic_year': academic_year,
                    'top_students': df.to_dict('records'),
                    'generated_date': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Error generating department performance report: {e}")
            return None
    
    def generate_comprehensive_performance_report(self, term: str, academic_year: str = '2024-2025') -> Dict:
        """Generate a comprehensive performance report covering all categories"""
        try:
            comprehensive_report = {
                'report_type': 'Comprehensive Performance Analysis',
                'term': term,
                'academic_year': academic_year,
                'generated_date': datetime.now().isoformat(),
                'school_name': self.school_name,
                'performance_data': {}
            }
            
            # Best performers by class (Forms 1-4)
            comprehensive_report['performance_data']['by_class'] = {}
            for form_level in [1, 2, 3, 4]:
                class_report = self.get_best_performing_students_by_class(form_level, term, academic_year, 5)
                if class_report:
                    comprehensive_report['performance_data']['by_class'][f'Form_{form_level}'] = class_report
            
            # Best performers by subject
            comprehensive_report['performance_data']['by_subject'] = {}
            for subject in self.all_subjects:
                subject_report = self.get_best_performing_students_by_subject(subject, term, academic_year, 5)
                if subject_report:
                    comprehensive_report['performance_data']['by_subject'][subject] = subject_report
            
            # Best performers by department
            comprehensive_report['performance_data']['by_department'] = {}
            for department in self.departments.keys():
                dept_report = self.get_best_performing_students_by_department(department, term, academic_year, 5)
                if dept_report:
                    comprehensive_report['performance_data']['by_department'][department] = dept_report
            
            return comprehensive_report
            
        except Exception as e:
            print(f"Error generating comprehensive performance report: {e}")
            return None
    
    def format_class_performance_report(self, report_data: Dict) -> str:
        """Format class performance report for display/printing"""
        if not report_data or not report_data.get('top_students'):
            return "No performance data available"
        
        report = f"""
{'='*90}
                            REPUBLIC OF MALAWI
                         MINISTRY OF EDUCATION
                      
                    [🇲🇼 MALAWI GOVERNMENT EMBLEM 🇲🇼]
                         UNITY - WORK - PROGRESS
                        
{'='*90}

                  BEST PERFORMING STUDENTS REPORT
                           {report_data['report_type']}

{'='*90}
SCHOOL: {self.school_name}
ACADEMIC YEAR: {report_data['academic_year']}
TERM: {report_data['term']}
REPORT GENERATED: {datetime.now().strftime('%d/%m/%Y at %H:%M')}

{'='*90}
TOP PERFORMING STUDENTS - FORM {report_data['form_level']}
{'='*90}

{'Rank':<6} {'Student No':<12} {'Full Name':<25} {'Average':<8} {'Subjects':<8} {'Passed':<7} {'Range':<12}
{'-'*90}
"""
        
        for i, student in enumerate(report_data['top_students'], 1):
            name = f"{student['first_name']} {student['last_name']}"
            range_marks = f"{student['lowest_mark']:.0f}-{student['highest_mark']:.0f}%"
            
            report += f"{i:<6} {student['student_number']:<12} {name[:24]:<25} "
            report += f"{student['overall_average']:.1f}%{'':<2} {student['subjects_taken']:<8} "
            report += f"{student['subjects_passed']:<7} {range_marks:<12}\n"
        
        # Add footer with official receipt info
        receipt_number = datetime.now().strftime('%Y%m%d%H%M%S')
        receipt_datetime = datetime.now().strftime('%d/%m/%Y at %H:%M:%S')
        
        report += f"""

{'='*90}
PERFORMANCE ANALYSIS:
{'='*90}

Excellence Recognition: These students have demonstrated outstanding academic 
performance in Form {report_data['form_level']} during {report_data['term']} {report_data['academic_year']}.

Ranking Criteria:
1. Overall Average Percentage (Primary)
2. Number of Subjects Passed (Secondary)
3. Consistency across subjects

{'='*90}
                        END OF PERFORMANCE REPORT
{'='*90}

{'-'*90}
Official Performance Report No: {receipt_number} ({receipt_datetime})
Created by: RN_LAB_TECH
{'-'*90}

"""
        return report
    
    def format_subject_performance_report(self, report_data: Dict) -> str:
        """Format subject performance report for display/printing"""
        if not report_data or not report_data.get('top_students'):
            return "No performance data available"
        
        report = f"""
{'='*90}
                            REPUBLIC OF MALAWI
                         MINISTRY OF EDUCATION
                      
                    [🇲🇼 MALAWI GOVERNMENT EMBLEM 🇲🇼]
                         UNITY - WORK - PROGRESS
                        
{'='*90}

                  BEST PERFORMING STUDENTS REPORT
                           {report_data['report_type']}

{'='*90}
SCHOOL: {self.school_name}
SUBJECT: {report_data['subject_name']}
ACADEMIC YEAR: {report_data['academic_year']}
TERM: {report_data['term']}
REPORT GENERATED: {datetime.now().strftime('%d/%m/%Y at %H:%M')}

{'='*90}
TOP PERFORMERS IN {report_data['subject_name'].upper()}
{'='*90}

{'Rank':<6} {'Student No':<12} {'Full Name':<25} {'Form':<6} {'Mark':<8} {'Grade':<6} {'Teacher':<20}
{'-'*90}
"""
        
        for i, student in enumerate(report_data['top_students'], 1):
            name = f"{student['first_name']} {student['last_name']}"
            
            report += f"{i:<6} {student['student_number']:<12} {name[:24]:<25} "
            report += f"{student['grade_level']:<6} {student['percentage']:.1f}%{'':<2} "
            report += f"{student['letter_grade']:<6} {student['teacher_name'][:19]:<20}\n"
        
        # Add footer with official receipt info
        receipt_number = datetime.now().strftime('%Y%m%d%H%M%S')
        receipt_datetime = datetime.now().strftime('%d/%m/%Y at %H:%M:%S')
        
        report += f"""

{'='*90}
SUBJECT PERFORMANCE ANALYSIS:
{'='*90}

Subject Excellence: These students achieved the highest marks in 
{report_data['subject_name']} during {report_data['term']} {report_data['academic_year']}.

Recognition: Outstanding achievement in {report_data['subject_name']} 
demonstrates dedication and mastery of the subject content.

{'='*90}
                        END OF SUBJECT REPORT
{'='*90}

{'-'*90}
Official Performance Report No: {receipt_number} ({receipt_datetime})
Created by: RN_LAB_TECH
{'-'*90}

"""
        return report
    
    def format_department_performance_report(self, report_data: Dict) -> str:
        """Format department performance report for display/printing"""
        if not report_data or not report_data.get('top_students'):
            return "No performance data available"
        
        subjects_list = ', '.join(report_data['department_subjects'])
        
        report = f"""
{'='*90}
                            REPUBLIC OF MALAWI
                         MINISTRY OF EDUCATION
                      
                    [🇲🇼 MALAWI GOVERNMENT EMBLEM 🇲🇼]
                         UNITY - WORK - PROGRESS
                        
{'='*90}

                  BEST PERFORMING STUDENTS REPORT
                           {report_data['report_type']}

{'='*90}
SCHOOL: {self.school_name}
DEPARTMENT: {report_data['department_name']}
SUBJECTS INCLUDED: {subjects_list}
ACADEMIC YEAR: {report_data['academic_year']}
TERM: {report_data['term']}
REPORT GENERATED: {datetime.now().strftime('%d/%m/%Y at %H:%M')}

{'='*90}
TOP PERFORMERS - {report_data['department_name'].upper()} DEPARTMENT
{'='*90}

{'Rank':<6} {'Student No':<12} {'Full Name':<25} {'Form':<6} {'Avg':<8} {'Subjects':<8} {'Passed':<7}
{'-'*90}
"""
        
        for i, student in enumerate(report_data['top_students'], 1):
            name = f"{student['first_name']} {student['last_name']}"
            
            report += f"{i:<6} {student['student_number']:<12} {name[:24]:<25} "
            report += f"{student['grade_level']:<6} {student['department_average']:.1f}%{'':<2} "
            report += f"{student['subjects_taken_in_dept']:<8} {student['subjects_passed_in_dept']:<7}\n"
        
        # Add footer with official receipt info
        receipt_number = datetime.now().strftime('%Y%m%d%H%M%S')
        receipt_datetime = datetime.now().strftime('%d/%m/%Y at %H:%M:%S')
        
        report += f"""

{'='*90}
DEPARTMENT PERFORMANCE ANALYSIS:
{'='*90}

Department Excellence: These students demonstrated exceptional performance 
across multiple subjects in the {report_data['department_name']} Department.

Subjects Evaluated: {subjects_list}

Recognition Criteria:
- Average performance across department subjects
- Minimum of 2 subjects taken in the department
- Consistency in department subject performance

{'='*90}
                     END OF DEPARTMENT REPORT
{'='*90}

{'-'*90}
Official Performance Report No: {receipt_number} ({receipt_datetime})
Created by: RN_LAB_TECH
{'-'*90}

"""
        return report
    
    def export_performance_report(self, report_type: str, **kwargs) -> str:
        """Export performance report to file"""
        try:
            if report_type == 'class':
                report_data = self.get_best_performing_students_by_class(**kwargs)
                formatted_report = self.format_class_performance_report(report_data)
                filename = f"Best_Performers_Form_{kwargs['form_level']}_{kwargs['term']}_{kwargs.get('academic_year', '2024-2025').replace('-', '_')}.txt"
            
            elif report_type == 'subject':
                report_data = self.get_best_performing_students_by_subject(**kwargs)
                formatted_report = self.format_subject_performance_report(report_data)
                subject_clean = kwargs['subject_name'].replace('/', '_').replace(' ', '_')
                filename = f"Best_Performers_{subject_clean}_{kwargs['term']}_{kwargs.get('academic_year', '2024-2025').replace('-', '_')}.txt"
            
            elif report_type == 'department':
                report_data = self.get_best_performing_students_by_department(**kwargs)
                formatted_report = self.format_department_performance_report(report_data)
                filename = f"Best_Performers_{kwargs['department_name']}_Dept_{kwargs['term']}_{kwargs.get('academic_year', '2024-2025').replace('-', '_')}.txt"
            
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            if formatted_report and "No performance data available" not in formatted_report:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(formatted_report)
                print(f"✅ Performance report exported to: {filename}")
                return filename
            else:
                print("❌ No data to export")
                return None
                
        except Exception as e:
            print(f"❌ Error exporting performance report: {e}")
            return None
    
    def export_rankings_to_excel(self, form_level: int, term: str, academic_year: str) -> str:
        """Export rankings to Excel file"""
        try:
            rankings = self.db.get_student_rankings(form_level, term, academic_year)
            
            if not rankings:
                return None
            
            import pandas as pd
            df = pd.DataFrame(rankings)
            
            filename = f"Form_{form_level}_Rankings_{term}_{academic_year.replace('-', '_')}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Rankings', index=False)
                
                # Add summary sheet
                summary_data = {
                    'Total Students': [len(rankings)],
                    'Students Passed': [len([r for r in rankings if r['status'] == 'PASS'])],
                    'Students Failed': [len([r for r in rankings if r['status'] == 'FAIL'])],
                    'Average Mark': [sum(r['average'] for r in rankings) / len(rankings)]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            return filename
            
        except Exception as e:
            print(f"Error exporting rankings to Excel: {e}")
            return None


def main():
    """Demo function showing performance analysis capabilities"""
    print("📊 PERFORMANCE ANALYZER MODULE")
    print("=" * 60)
    print("🏆 GENERATES BEST PERFORMING STUDENTS REPORTS:")
    print("   • By Class (Forms 1-4)")
    print("   • By Subject (All 12 subjects)")
    print("   • By Department (Sciences, Humanities, Languages)")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer("DEMO SECONDARY SCHOOL")
    
    print("\n🔬 DEPARTMENT CLASSIFICATIONS:")
    for dept, info in analyzer.departments.items():
        print(f"\n{dept} Department:")
        for subject in info['subjects']:
            print(f"  • {subject}")
    
    print("\n" + "=" * 60)
    print("💡 USAGE EXAMPLES:")
    print("=" * 60)
    
    print("\n1. Best performers by class:")
    print("   analyzer.get_best_performing_students_by_class(form_level=1, term='Term 1')")
    
    print("\n2. Best performers by subject:")
    print("   analyzer.get_best_performing_students_by_subject('Mathematics', term='Term 1')")
    
    print("\n3. Best performers by department:")
    print("   analyzer.get_best_performing_students_by_department('Sciences', term='Term 1')")
    
    print("\n4. Export performance report:")
    print("   analyzer.export_performance_report('class', form_level=1, term='Term 1')")
    
    print("\n5. Comprehensive analysis:")
    print("   analyzer.generate_comprehensive_performance_report(term='Term 1')")
    
    print("\n✅ Performance analysis system ready!")


if __name__ == "__main__":
    main()
