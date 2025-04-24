import pytest
from datetime import datetime, timedelta
from app import db
from app import User, GroceryItem

def test_user_creation():
    """Test User model creation and validation"""
    user = User(
        username='testuser',
        email='test@example.com',
        password='hashed_password'
    )
    db.session.add(user)
    db.session.commit()

    assert user.id is not None
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.dark_mode is False
    assert user.notification_days == 3

def test_grocery_item_creation():
    """Test GroceryItem model creation and validation"""
    user = User(username='testuser', email='test@example.com', password='pass')
    db.session.add(user)
    db.session.commit()

    item = GroceryItem(
        name='Milk',
        category='Dairy',
        quantity='1 gallon',
        expiry_date=datetime.now().date() + timedelta(days=7),
        user_id=user.id
    )
    db.session.add(item)
    db.session.commit()

    assert item.id is not None
    assert item.name == 'Milk'
    assert item.category == 'Dairy'
    assert item.status == 'active'

def test_user_grocery_items_relationship():
    """Test relationship between User and GroceryItem models"""
    user = User(username='testuser', email='test@example.com', password='pass')
    db.session.add(user)
    db.session.commit()

    item1 = GroceryItem(
        name='Milk',
        category='Dairy',
        quantity='1 gallon',
        expiry_date=datetime.now().date() + timedelta(days=7),
        user_id=user.id
    )
    item2 = GroceryItem(
        name='Bread',
        category='Bakery',
        quantity='1 loaf',
        expiry_date=datetime.now().date() + timedelta(days=5),
        user_id=user.id
    )
    db.session.add_all([item1, item2])
    db.session.commit()

    # Query the items through the user relationship
    user_items = GroceryItem.query.filter_by(user_id=user.id).all()
    assert len(user_items) == 2
    assert user_items[0].name == 'Milk'
    assert user_items[1].name == 'Bread'