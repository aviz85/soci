# SociSphere

SociSphere is a modern social media platform built with Django and modern frontend technologies.

## Features

- User authentication and profiles
- Social media feed with posts, comments, and likes
- Real-time notifications
- Direct messaging
- Community groups
- Responsive design for all devices

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Docker, Nginx

## Project Structure

```
/soci/
├── socisphere/           # Django project settings
├── templates/            # HTML templates
├── static/               # Static assets
│   ├── css/              # CSS files (modular architecture)
│   ├── js/               # JavaScript files
│   └── img/              # Images and media
├── tests/                # Test suite
└── manage.py             # Django management script
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/socisphere.git
   cd socisphere
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
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

7. Visit `http://127.0.0.1:8000/` in your browser.

## Development

### CSS Architecture

The CSS follows a modular architecture for better maintainability. See the [CSS README](/static/css/README.md) for details.

### JavaScript

The JavaScript is organized into modules:
- `main.js`: Core functionality and initialization
- `navbar.js`: Navigation and responsive menu
- `api.js`: API interaction functions

### Testing

Run the test suite:
```
python manage.py test
```

For frontend tests:
```
cd tests
pytest
```

## Deployment

### Docker

Build and run with Docker:
```
docker-compose up --build
```

### Manual Deployment

See the [deployment guide](docs/deployment.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Django](https://www.djangoproject.com/)
- [Font Awesome](https://fontawesome.com/) for icons
- All contributors and supporters 