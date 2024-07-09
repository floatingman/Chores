# Django Chore Tracker

Django Chore Tracker is a web application designed to help families manage and track household chores. It allows parents to assign chores to children, set point values for chores, and track completion.

## Features

- Create and manage children profiles
- Create and manage chore listings
- Assign chores to children
- Track chore completion and point accumulation
- View chore completion statistics and graphs

## Technologies Used

- Python 3.8+
- Django 3.2+
- SQLite (default database)
- HTML/CSS
- Bootstrap 5
- Chart.js (for graphs)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/django-chore-tracker.git
   cd django-chore-tracker
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Open a web browser and navigate to `http://localhost:8000` to access the application.

## Usage

1. Log in with your superuser account.
2. Add children profiles through the admin interface or the application interface.
3. Create chores with point values.
4. Assign chores to children.
5. Mark chores as completed when children finish them.
6. View statistics and graphs to track progress.

## Project Structure

- `chore_tracker/` - Main Django app directory
    - `models.py` - Database models (Child, Chore, ChoreAssignment)
    - `views.py` - View functions and classes
    - `forms.py` - Form classes for data input
    - `urls.py` - URL configurations
    - `templates/` - HTML templates
    - `static/` - Static files (CSS, JavaScript)
- `django_chore_tracker/` - Project settings directory
- `manage.py` - Django's command-line utility for administrative tasks

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django documentation
- Bootstrap documentation
- Chart.js documentation