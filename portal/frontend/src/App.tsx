// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useState, useEffect } from 'react';
import { ProcessOrderButton } from './components/ProcessOrderButton';
import { ResetButton } from './components/ResetButton';
import { IncidentBanner } from './components/IncidentBanner';
import { ArchitectureDiagram } from './components/ArchitectureDiagram';
import { BusinessDiagram } from './components/BusinessDiagram';
import { LambdaInvocationResult } from './api/client';
import { apiClient } from './api/client';

// Main App component - Business-focused demo portal
// Shows business view by default with toggle for technical details

function App() {
  const [invocationError, setInvocationError] = useState<string | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [incidentStartTime, setIncidentStartTime] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [resolutionTime, setResolutionTime] = useState<number | null>(null);
  const [alarmTriggered, setAlarmTriggered] = useState(false);
  const [alarmData, setAlarmData] = useState<{
    reason: string;
    updatedAt: string;
    alarmName: string;
    alarmDescription: string;
    metricName: string;
    namespace: string;
    threshold: number;
    comparisonOperator: string;
    period: number;
  } | null>(null);

  const handleInvocationResult = (result: LambdaInvocationResult | null, error: string | null) => {
    console.log('Invocation result:', result);
    if (error) {
      // Start timer when incident occurs
      setIncidentStartTime(Date.now());
      setInvocationError(error);
      setIsTimerRunning(true);
      setResolutionTime(null);
    } else {
      // Clear incident on success
      setIncidentStartTime(null);
      setInvocationError(null);
      setElapsedTime(0);
      setIsTimerRunning(false);
      setResolutionTime(null);
    }
  };

  const handleRootCauseFound = () => {
    // Stop timer and record resolution time
    if (incidentStartTime) {
      const finalTime = Math.floor((Date.now() - incidentStartTime) / 1000);
      setResolutionTime(finalTime);
      setIsTimerRunning(false);
    }
  };

  const handleReset = () => {
    // Clear all state - back to clean screen
    setInvocationError(null);
    setIncidentStartTime(null);
    setElapsedTime(0);
    setIsTimerRunning(false);
    setResolutionTime(null);
  };

  // Timer effect
  useEffect(() => {
    if (incidentStartTime && isTimerRunning) {
      const interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - incidentStartTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [incidentStartTime, isTimerRunning]);

  // Poll alarm status when incident is active
  useEffect(() => {
    if (incidentStartTime && isTimerRunning) {
      const checkAlarm = async () => {
        try {
          const response = await apiClient.getAlarmStatus();
          if (response.success && response.data) {
            const data = response.data;
            if (data.exists && data.state === 'ALARM') {
              setAlarmTriggered(true);
              setAlarmData({
                reason: data.reason || 'Alarm triggered',
                updatedAt: data.updatedAt || new Date().toISOString(),
                alarmName: data.alarmName || 'demo-lambda-errors',
                alarmDescription: data.alarmDescription || '',
                metricName: data.metricName || 'Errors',
                namespace: data.namespace || 'AWS/Lambda',
                threshold: data.threshold || 1,
                comparisonOperator: data.comparisonOperator || '≥',
                period: data.period || 1
              });
            }
          }
        } catch (error) {
          console.error('Failed to check alarm:', error);
        }
      };

      // Check immediately, then every 5 seconds
      checkAlarm();
      const interval = setInterval(checkAlarm, 5000);
      return () => clearInterval(interval);
    } else {
      setAlarmTriggered(false);
      setAlarmData(null);
    }
  }, [incidentStartTime, isTimerRunning]);

  const isOperational = !invocationError;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-orange-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">
            AWS DevOps Agent Demo
          </h1>
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors duration-200 text-sm font-medium"
          >
            {showTechnicalDetails ? '← Business View' : 'Show Technical Details →'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Diagram - Business or Technical based on toggle */}
        {showTechnicalDetails ? (
          <ArchitectureDiagram />
        ) : (
          <BusinessDiagram isOperational={isOperational} />
        )}

        {/* Incident Banner - Only show when incident is active */}
        {incidentStartTime && (
          <IncidentBanner
            incidentStartTime={incidentStartTime}
            elapsedTime={elapsedTime}
            resolutionTime={resolutionTime}
            isTimerRunning={isTimerRunning}
            alarmTriggered={alarmTriggered}
            alarmData={alarmData}
            onRootCauseFound={handleRootCauseFound}
          />
        )}

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8 mb-6">
          <div className="flex gap-4 justify-center">
            <ProcessOrderButton onResult={handleInvocationResult} />
            <ResetButton onReset={handleReset} />
          </div>
        </div>
      </main>


    </div>
  );
}

export default App;
