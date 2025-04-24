import '@testing-library/jest-dom';
import { fireEvent } from '@testing-library/dom';

describe('Dark Mode', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="dark-mode-toggle">
        <input type="checkbox" id="darkModeToggle">
      </div>
      <div class="content"></div>
    `;
  });

  test('toggles dark mode classes', () => {
    const toggle = document.getElementById('darkModeToggle');
    const content = document.querySelector('.content');

    // Initial state
    expect(content.classList.contains('dark-mode')).toBeFalsy();

    // Enable dark mode
    fireEvent.click(toggle);
    expect(content.classList.contains('dark-mode')).toBeTruthy();

    // Disable dark mode
    fireEvent.click(toggle);
    expect(content.classList.contains('dark-mode')).toBeFalsy();
  });
}); 