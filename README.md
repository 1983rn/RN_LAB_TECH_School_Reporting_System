# Malawi School Reporting System

A comprehensive web-based student management and report generation system designed for Malawi secondary schools. Features responsive data entry, PDF report generation, and professional Malawi flag-themed UI design.

## 🎯 Key Features

- **Multi-Form Support**: Data entry for Forms 1-4 with subject-specific mark recording
- **Responsive Design**: Mobile-friendly interface with sticky headers and no horizontal scrolling
- **PDF Report Generation**: Individual student report cards with professional formatting
- **Quick Actions**: One-click print buttons for each student, bulk operations support
- **Malawi Theming**: Beautiful UI with national flag colors (green, red, black, gold)
- **Real-time Validation**: Input validation and error handling for data integrity

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with custom ORM
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **PDF Generation**: ReportLab library
- **Styling**: Custom CSS with Malawi flag color scheme

---

## Deployment on Render.com

This application is ready for deployment on Render.

### Using `render.yaml` (Recommended)
1. Push your code to a GitHub/GitLab repository.
2. On the Render dashboard, create a new **Blueprint** service.
3. Connect your repository. Render will automatically detect and use the `render.yaml` file to configure the web service.

### Manual Configuration
1. On the Render dashboard, create a new **Web Service**.
2. Set the **Build Command** to: `pip install -r requirements.txt`
3. Set the **Start Command** to: `gunicorn wsgi:app`
