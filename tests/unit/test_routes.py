def test_home_page_redirect(client):
    """Test that home page redirects to login when not authenticated"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_register(client):
    """Test user registration"""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123'
    })
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_logout(client):
    """Test login and logout functionality"""
    # Register a user
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })

    # Test login
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 302
    assert '/' in response.headers['Location']

    # Test logout
    response = client.get('/logout')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_add_item(auth_client, sample_item):
    """Test adding a grocery item"""
    response = auth_client.post('/add_item', data=sample_item)
    assert response.status_code == 302
    assert '/' in response.headers['Location']

def test_update_item(auth_client, sample_item):
    """Test updating a grocery item"""
    # First add an item
    response = auth_client.post('/add_item', data=sample_item)
    assert response.status_code == 302

    # Then update it
    updated_data = sample_item.copy()
    updated_data['name'] = 'Updated Item'
    response = auth_client.post('/update_item/1', data=updated_data)
    assert response.status_code == 302

    # Verify the update
    response = auth_client.get('/')
    assert b'Updated Item' in response.data

def test_delete_item(auth_client, sample_item):
    """Test deleting a grocery item"""
    # First add an item
    auth_client.post('/add_item', data=sample_item)

    # Then delete it
    response = auth_client.get('/delete_item/1')
    assert response.status_code == 302

    # Verify the deletion
    response = auth_client.get('/')
    assert sample_item['name'].encode() not in response.data 