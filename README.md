# SociSphere

SociSphere is a modern social networking platform that allows users to connect, share content, join communities, and interact with each other.

## Features

- **User Authentication**: Secure login and registration system
- **Content Sharing**: Create, view, and interact with posts
- **Communities**: Create and join communities based on interests
- **Messaging**: Real-time private messaging between users
- **Notifications**: Stay updated with activity related to your account
- **User Profiles**: Customizable user profiles with activity history

## Project Structure

The project consists of two main components:

1. **Backend API**: Django REST Framework-based API (running on port 8080)
2. **Frontend UI**: HTML, CSS, and JavaScript-based UI (running on port 3000)

### Backend API

The backend API is built with Django and provides endpoints for all the functionality of the platform. It handles:

- User authentication and management
- Content creation and retrieval
- Community management
- Messaging and notifications
- User interactions (follows, likes, etc.)

### Frontend UI

The frontend is built with vanilla HTML, CSS, and JavaScript, providing a responsive and intuitive user interface. It includes:

- Modern, responsive design
- Interactive components
- Real-time updates for messages and notifications
- Comprehensive error handling

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Clone the repository
2. Navigate to the project directory
3. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Start the server:
   ```
   python manage.py runserver 8080
   ```

### Frontend Setup

1. Navigate to the project directory
2. Install dependencies:
   ```
   npm install
   ```
3. Start the server:
   ```
   npm start
   ```
4. Access the application at `http://localhost:3000`

## API Documentation

The API provides the following main endpoints:

- `/api/auth/`: Authentication endpoints
- `/api/users/`: User management endpoints
- `/api/content/`: Content creation and retrieval endpoints
- `/api/communities/`: Community management endpoints
- `/api/interactions/`: User interaction endpoints (follows, messages, notifications)

For detailed API documentation, run the server and visit `http://localhost:8080/api/docs/`

## Technologies Used

- **Backend**:
  - Django
  - Django REST Framework
  - PostgreSQL
  - JWT Authentication

- **Frontend**:
  - HTML5
  - CSS3
  - JavaScript (ES6+)
  - Express.js (for serving static files)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Icons from Font Awesome
- Design inspiration from modern social platforms

## Testing

Run tests with pytest:

```
python -m pytest
```

Run tests with coverage:

```
coverage run --source=apps -m pytest && coverage report
```

## API Client Example

A simple Python client for testing the API is included in `test_api.py`. To use it:

```
./test_api.py
```

## Project Structure

- `apps/users/`: User management
- `apps/content/`: Content creation and discovery
- `apps/communities/`: Community features
- `apps/interactions/`: Social interactions
- `tests/`: Test suite

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request 