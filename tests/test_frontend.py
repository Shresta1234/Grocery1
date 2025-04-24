from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest
import time

@pytest.fixture
def driver():
    # Setup Chrome in headless mode
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run tests without opening browser window
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_login_page(driver):
    """Test the login page loads correctly"""
    driver.get('http://localhost:5000/login')
    assert "Login" in driver.title
    
    # Check for login form elements
    username_input = driver.find_element(By.NAME, 'username')
    password_input = driver.find_element(By.NAME, 'password')
    submit_button = driver.find_element(By.TAG_NAME, 'button')
    
    assert username_input.is_displayed()
    assert password_input.is_displayed()
    assert submit_button.is_displayed()

def test_add_item_workflow(driver):
    """Test adding a new grocery item"""
    # Login first
    driver.get('http://localhost:5000/login')
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.TAG_NAME, 'form').submit()
    
    # Wait for redirect to home page
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'addItemModal'))
    )
    
    # Click add item button
    driver.find_element(By.CSS_SELECTOR, '[data-bs-toggle="modal"]').click()
    
    # Wait for modal to appear
    modal = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'addItemModal'))
    )
    
    # Fill in the form
    modal.find_element(By.NAME, 'name').send_keys('Test Item')
    modal.find_element(By.NAME, 'category').send_keys('Dairy')
    modal.find_element(By.NAME, 'quantity').send_keys('1')
    modal.find_element(By.NAME, 'expiry_date').send_keys('2024-12-31')
    
    # Submit form
    modal.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    
    # Wait for page to refresh and verify item was added
    time.sleep(1)  # Wait for page refresh
    items = driver.find_elements(By.CSS_SELECTOR, 'td')
    assert any('Test Item' in item.text for item in items)

def test_toggle_view(driver):
    """Test toggling between table and card views"""
    # Login first
    driver.get('http://localhost:5000/login')
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.TAG_NAME, 'form').submit()
    
    # Wait for page to load
    toggle_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'toggleView'))
    )
    
    # Get initial view state
    container = driver.find_element(By.ID, 'itemsContainer')
    initial_view = 'table-view' in container.get_attribute('class')
    
    # Click toggle button
    toggle_button.click()
    time.sleep(1)  # Wait for animation
    
    # Verify view changed
    container = driver.find_element(By.ID, 'itemsContainer')
    new_view = 'table-view' in container.get_attribute('class')
    assert initial_view != new_view

def test_dark_mode(driver):
    """Test dark mode toggle"""
    # Login and navigate to settings
    driver.get('http://localhost:5000/login')
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.TAG_NAME, 'form').submit()
    
    # Go to settings page
    driver.get('http://localhost:5000/settings')
    
    # Find and click dark mode toggle
    dark_mode_toggle = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'dark_mode'))
    )
    initial_state = dark_mode_toggle.is_selected()
    dark_mode_toggle.click()
    
    # Submit form
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    
    # Verify dark mode changed
    time.sleep(1)  # Wait for page refresh
    body_class = driver.find_element(By.TAG_NAME, 'body').get_attribute('class')
    if initial_state:
        assert 'bg-light' in body_class
    else:
        assert 'bg-dark' in body_class 