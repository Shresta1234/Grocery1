import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def browser():
    """Selenium WebDriver fixture"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_add_item_flow(browser, live_server):
    """Test the complete flow of adding a grocery item"""
    # Start the live server
    url = live_server.url()

    # Register and login
    browser.get(f"{url}/register")
    browser.find_element(By.NAME, "username").send_keys("testuser")
    browser.find_element(By.NAME, "email").send_keys("test@example.com")
    browser.find_element(By.NAME, "password").send_keys("testpass123")
    browser.find_element(By.TAG_NAME, "form").submit()

    # Login
    browser.get(f"{url}/login")
    browser.find_element(By.NAME, "username").send_keys("testuser")
    browser.find_element(By.NAME, "password").send_keys("testpass123")
    browser.find_element(By.TAG_NAME, "form").submit()

    # Add an item
    browser.find_element(By.CSS_SELECTOR, "[data-bs-target='#addItemModal']").click()
    
    # Wait for modal to appear
    modal = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "addItemModal"))
    )
    
    # Fill in the form
    modal.find_element(By.NAME, "name").send_keys("Test Item")
    modal.find_element(By.NAME, "category").send_keys("Dairy")
    modal.find_element(By.NAME, "quantity").send_keys("1")
    modal.find_element(By.NAME, "expiry_date").send_keys("2024-12-31")
    modal.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Verify item was added
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Test Item')]"))
    )

def test_view_toggle(browser, live_server):
    """Test toggling between table and card views"""
    url = live_server.url()
    browser.get(url)

    # Click the toggle view button
    toggle_btn = browser.find_element(By.ID, "toggleView")
    toggle_btn.click()

    # Verify the view changed
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".card-view"))
    )

    # Toggle back
    toggle_btn.click()
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".table-view"))
    ) 