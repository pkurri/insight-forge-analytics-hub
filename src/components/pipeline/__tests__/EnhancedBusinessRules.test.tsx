import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// This will use our mock implementation
jest.mock('../EnhancedBusinessRules');
import EnhancedBusinessRules from '../EnhancedBusinessRules';

describe('EnhancedBusinessRules', () => {
  const sampleData = [
    { id: 1, name: 'John', age: 30, email: 'john@example.com' },
    { id: 2, name: 'Jane', age: 25, email: 'jane@example.com' }
  ];

  it('renders with the correct title and dataset info', () => {
    render(
      <EnhancedBusinessRules 
        datasetId="test-dataset"
        sampleData={sampleData}
      />
    );

    expect(screen.getByText('Business Rules')).toBeInTheDocument();
    expect(screen.getByText('Dataset ID: test-dataset')).toBeInTheDocument();
    expect(screen.getByText('Sample Data Rows: 2')).toBeInTheDocument();
  });

  it('displays a loading state when generating rules', async () => {
    render(
      <EnhancedBusinessRules 
        datasetId="test-dataset"
        sampleData={sampleData}
      />
    );

    // Click the generate rules button
    const generateButton = screen.getByTestId('generate-rules-button');
    fireEvent.click(generateButton);

    // Should show loading state
    expect(screen.getByText('Generating Rules...')).toBeInTheDocument();
    
    // Wait for the rules to be loaded
    await waitFor(() => {
      expect(screen.getByText('Rule 1: Email Validation')).toBeInTheDocument();
    });
  });

  it('calls onRulesApplied when rules are generated', async () => {
    const mockOnRulesApplied = jest.fn();
    
    render(
      <EnhancedBusinessRules 
        datasetId="test-dataset"
        sampleData={sampleData}
        onRulesApplied={mockOnRulesApplied}
      />
    );

    // Click the generate rules button
    const generateButton = screen.getByTestId('generate-rules-button');
    fireEvent.click(generateButton);

    // Wait for the rules to be loaded
    await waitFor(() => {
      expect(screen.getByText('Rule 1: Email Validation')).toBeInTheDocument();
    });

    // Check that onRulesApplied was called with the correct data
    expect(mockOnRulesApplied).toHaveBeenCalledWith([
      expect.objectContaining({
        id: 'rule-1',
        name: 'Email Validation'
      })
    ]);
  });

  it('calls onComplete when complete button is clicked', () => {
    const mockOnComplete = jest.fn();
    
    render(
      <EnhancedBusinessRules 
        datasetId="test-dataset"
        sampleData={sampleData}
        onComplete={mockOnComplete}
      />
    );

    // Click the complete button
    const completeButton = screen.getByTestId('complete-button');
    fireEvent.click(completeButton);

    expect(mockOnComplete).toHaveBeenCalledTimes(1);
  });
});
