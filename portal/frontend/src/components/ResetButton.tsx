// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useState } from 'react';
import { apiClient } from '../api/client';

interface ResetButtonProps {
  onReset: () => void;
}

export function ResetButton({ onReset }: ResetButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    setLoading(true);
    
    try {
      // Call backend to clear CloudWatch Alarm and logs
      await apiClient.resetDemo();
      
      // Clear UI state
      onReset();
    } catch (error) {
      console.error('Failed to reset:', error);
      // Still clear UI even if backend call fails
      onReset();
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleReset}
      disabled={loading}
      className={`
        px-8 py-4 text-lg font-medium rounded-xl transition-all duration-200
        ${loading 
          ? 'bg-slate-300 cursor-not-allowed text-slate-500 shadow-none'
          : 'bg-orange-500 hover:bg-orange-600 text-white hover:-translate-y-0.5 active:translate-y-0 shadow-lg hover:shadow-xl'
        }
      `}
    >
      {loading ? 'Resetting...' : 'Reset Demo'}
    </button>
  );
}
