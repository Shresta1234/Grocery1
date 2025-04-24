import '@testing-library/jest-dom';
import { fireEvent } from '@testing-library/dom';
import '../static/js/app.js';

describe('Grocery Tracker Frontend', () => {
  beforeEach(() => {
    // Reset fetch mock
    fetch.mockReset();
    
    // Reset localStorage
    localStorage.clear();
    
    // Reset DOM
    document.body.innerHTML = `
      <div id="itemsContainer">
        <div class="table-responsive">
          <table id="itemsTable"></table>
        </div>
        <div class="row"></div>
      </div>
      <button id="toggleView">Toggle View</button>
      <canvas id="expiryChart"></canvas>
    `;
  });

  test('toggles view between table and card view', () => {
    const container = document.getElementById('itemsContainer');
    const toggleBtn = document.getElementById('toggleView');

    // Initial state should be table view
    expect(container.classList.contains('table-view')).toBeTruthy();
    expect(container.classList.contains('card-view')).toBeFalsy();

    // Click toggle button
    fireEvent.click(toggleBtn);

    // Should switch to card view
    expect(container.classList.contains('card-view')).toBeTruthy();
    expect(container.classList.contains('table-view')).toBeFalsy();

    // Click toggle button again
    fireEvent.click(toggleBtn);

    // Should switch back to table view
    expect(container.classList.contains('table-view')).toBeTruthy();
    expect(container.classList.contains('card-view')).toBeFalsy();
  });

  test('saves view preference to localStorage', () => {
    const toggleBtn = document.getElementById('toggleView');

    // Click toggle button to switch to card view
    fireEvent.click(toggleBtn);

    // Check localStorage
    expect(localStorage.getItem('viewPreference')).toBe('card');

    // Click toggle button again to switch back to table view
    fireEvent.click(toggleBtn);

    // Check localStorage updated
    expect(localStorage.getItem('viewPreference')).toBe('table');
  });

  test('loads expiry chart data', async () => {
    // Mock API response
    const mockData = [
      { name: 'Milk', days_left: 2 },
      { name: 'Bread', days_left: 5 }
    ];

    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockData)
      })
    );

    // Wait for chart update
    await new Promise(resolve => setTimeout(resolve, 0));

    // Verify fetch was called with correct URL
    expect(fetch).toHaveBeenCalledWith('/api/expiring_soon');
  });

  test('handles form submission for adding items', () => {
    // Add form to DOM
    document.body.innerHTML += `
      <form id="addItemForm">
        <input name="name" value="Test Item">
        <input name="category" value="Dairy">
        <input name="quantity" value="1">
        <input name="expiry_date" value="2024-12-31">
        <button type="submit">Add</button>
      </form>
    `;

    const form = document.getElementById('addItemForm');
    const submitSpy = jest.spyOn(form, 'submit');
    submitSpy.mockImplementation(e => e.preventDefault());

    // Submit form
    fireEvent.submit(form);

    // Verify form submission
    expect(submitSpy).toHaveBeenCalled();
  });

  test('handles modal form pre-filling', () => {
    // Add modal form to DOM
    document.body.innerHTML += `
      <button 
        class="edit-item-btn" 
        data-item='{"name":"Test Item","category":"Dairy","quantity":"1","expiry_date":"2024-12-31"}'>
        Edit
      </button>
      <div id="editItemModal">
        <form>
          <input name="name">
          <input name="category">
          <input name="quantity">
          <input name="expiry_date">
        </form>
      </div>
    `;

    const editButton = document.querySelector('.edit-item-btn');
    
    // Click edit button
    fireEvent.click(editButton);

    // Verify form fields were pre-filled
    const form = document.querySelector('#editItemModal form');
    expect(form.elements.name.value).toBe('Test Item');
    expect(form.elements.category.value).toBe('Dairy');
    expect(form.elements.quantity.value).toBe('1');
    expect(form.elements.expiry_date.value).toBe('2024-12-31');
  });
}); 