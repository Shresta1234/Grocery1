import json
from datetime import datetime, timedelta

def test_expiring_soon_api(auth_client, sample_item):
    """Test the expiring items API endpoint"""
    # Add items with different expiry dates
    items = [
        {
            'name': 'Expiring Soon',
            'category': 'Dairy',
            'quantity': '1 gallon',
            'expiry_date': '2024-12-31'
        },
        {
            'name': 'Expiring Soon',
            'category': 'Dairy',
            'quantity': '1 gallon',
            'expiry_date': '2024-12-31'
        },
        {
            'name': 'Expiring Soon',
            'category': 'Dairy',
            'quantity': '1 gallon',
            'expiry_date': '2024-12-31'
        }
    ]

    # Add items to the database
    for item in items:
        auth_client.post('/add_item', data=item)

    # Verify the items are added correctly
    response = auth_client.get('/')
    assert b'Expiring Soon' in response.data

    # Verify the items are expiring soon
    expiring_items = json.loads(response.data)
    for item in expiring_items:
        expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
        assert expiry_date <= datetime.now().date() + timedelta(days=7)

    # Verify the items are in the correct category
    for item in expiring_items:
        assert item['category'] == 'Dairy'

    # Verify the items are in the correct quantity
    for item in expiring_items:
        assert item['quantity'] == '1 gallon'

    # Verify the items are in the correct expiry date
    for item in expiring_items:
        assert item['expiry_date'] == '2024-12-31' 