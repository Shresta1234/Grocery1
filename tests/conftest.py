import os
import tempfile
import pytest
from app import app, db

@pytest.fixture
def client():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def auth_client(client):
    """Authenticated client fixture"""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })
    return client

@pytest.fixture
def sample_item():
    """Sample grocery item data"""
    return {
        'name': 'Test Item',
        'category': 'Dairy',
        'quantity': '1 gallon',
        'expiry_date': '2024-12-31'
    } 