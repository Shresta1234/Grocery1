import '@testing-library/jest-dom';

describe('Expiry Chart', () => {
  beforeEach(() => {
    fetch.mockReset();
  });

  test('updates chart with new data', async () => {
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

    // Call updateExpiryChart
    await window.updateExpiryChart();

    // Verify Chart.js was called with correct data
    expect(Chart).toHaveBeenCalledWith(
      expect.any(Object),
      expect.objectContaining({
        type: 'bar',
        data: expect.objectContaining({
          labels: ['Milk', 'Bread'],
          datasets: expect.arrayContaining([
            expect.objectContaining({
              data: [2, 5]
            })
          ])
        })
      })
    );
  });

  test('handles API errors gracefully', async () => {
    // Mock console.error
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    // Mock failed API call
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('API Error'))
    );

    // Call updateExpiryChart
    await window.updateExpiryChart();

    // Verify error was logged
    expect(consoleSpy).toHaveBeenCalledWith('Error updating chart:', expect.any(Error));

    // Restore console.error
    consoleSpy.mockRestore();
  });
}); 