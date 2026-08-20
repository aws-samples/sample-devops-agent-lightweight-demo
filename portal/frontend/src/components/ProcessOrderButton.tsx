// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useState } from 'react';
import { apiClient, LambdaInvocationResult } from '../api/client';

// ProcessOrderButton component - Business-friendly order processing button
// - Calls POST /api/process-order endpoint
// - Shows loading state during invocation
// - Handles success and error responses with business-friendly messages

interface ProcessOrderButtonProps {
  onResult: (result: LambdaInvocationResult | null, error: string | null) => void;
}

export function ProcessOrderButton({ onResult }: ProcessOrderButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    
    try {
      const response = await apiClient.triggerLambda();
      
      if (response.success && response.data) {
        onResult(response.data, null);
      } else {
        onResult(null, response.error || 'Unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`
        px-8 py-4 text-lg font-medium rounded-xl
        transition-all duration-200
        ${isLoading 
          ? 'bg-slate-300 cursor-not-allowed text-slate-500 shadow-none' 
          : 'bg-sky-600 hover:bg-sky-700 text-white hover:-translate-y-0.5 active:translate-y-0'
        }
        shadow-lg hover:shadow-xl
      `}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
              fill="none"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Processing...
        </span>
      ) : (
        'Process Order'
      )}
    </button>
  );
}
