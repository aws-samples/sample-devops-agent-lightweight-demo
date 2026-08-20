// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// API client module with typed responses and error handling
// Requirements: 14.2

import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = ((window as any).__config?.apiUrl || '').replace(/\/+$/, '');

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface LambdaInvocationResult {
  statusCode?: number;
  body?: string;
  errorMessage?: string;
  errorType?: string;
}

class ApiClient {
  private baseUrl = API_BASE_URL;

  private async getAuthToken(): Promise<string | null> {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString() || null;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const token = await this.getAuthToken();
      
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          ...options.headers,
        },
      });

      const data = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      // If data is already wrapped with success field, return as-is
      if (typeof data === 'object' && data !== null && 'success' in data) {
        return data;
      }
      
      // If data is an array or plain object, wrap it
      return {
        success: true,
        data: data as T
      };
    } catch (error) {
      // Network failure or connection error
      if (error instanceof TypeError && error.message.includes('fetch')) {
        return {
          success: false,
          error: 'Cannot connect to backend. Is the server running?',
        };
      }
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'An unexpected error occurred',
      };
    }
  }

  async triggerLambda(): Promise<ApiResponse<LambdaInvocationResult>> {
    return this.request<LambdaInvocationResult>('/process-order', {
      method: 'POST',
    });
  }

  async resetDemo(): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>('/reset-demo', {
      method: 'POST',
    });
  }

  async getAlarmStatus(): Promise<ApiResponse<any>> {
    return this.request<any>('/alarm-status');
  }
}

export const apiClient = new ApiClient();
