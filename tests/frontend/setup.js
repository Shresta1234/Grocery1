import '@testing-library/jest-dom';

// Mock fetch API
global.fetch = jest.fn();

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: jest.fn().mockImplementation(() => ({
    destroy: jest.fn(),
    update: jest.fn()
  }))
}));

// Setup DOM elements that are always needed
document.body.innerHTML = `
  <div id="itemsContainer">
    <div class="table-responsive">
      <table id="itemsTable"></table>
    </div>
    <div class="row"></div>
  </div>
  <canvas id="expiryChart"></canvas>
`; 