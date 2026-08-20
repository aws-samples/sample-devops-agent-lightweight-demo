
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// IncidentBanner component - Shows incident status with timer
// Displays when orders are failing with business impact context

interface IncidentBannerProps {
  incidentStartTime: number;
  elapsedTime: number;
  resolutionTime: number | null;
  isTimerRunning: boolean;
  alarmTriggered: boolean;
  alarmData: {
    reason: string;
    updatedAt: string;
    alarmName: string;
    alarmDescription: string;
    metricName: string;
    namespace: string;
    threshold: number;
    comparisonOperator: string;
    period: number;
  } | null;
  onRootCauseFound: () => void;
}

export function IncidentBanner({
  incidentStartTime: _incidentStartTime,
  elapsedTime,
  resolutionTime,
  isTimerRunning,
  alarmTriggered,
  alarmData,
  onRootCauseFound
}: IncidentBannerProps) {
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-red-50 border-2 border-red-400 rounded-lg p-6 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-red-800 mb-2">⚠️ Incident Active</h2>
          <p className="text-red-700">Customer orders cannot be processed</p>
          {alarmTriggered && (
            <div className="relative group inline-block">
              <p className="text-red-600 text-sm mt-2 font-medium cursor-help">
                🚨 CloudWatch Alarm triggered
              </p>
              {alarmData && (
                <div className="absolute left-0 top-full mt-2 w-96 bg-slate-900 text-white text-xs rounded-lg p-3 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                  <div className="mb-2">
                    <span className="font-semibold">Alarm:</span> {alarmData.alarmName}
                  </div>
                  {alarmData.alarmDescription && (
                    <div className="mb-2">
                      <span className="font-semibold">Description:</span> {alarmData.alarmDescription}
                    </div>
                  )}
                  <div className="mb-2">
                    <span className="font-semibold">Metric:</span> {alarmData.metricName} ({alarmData.namespace})
                  </div>
                  <div className="mb-2">
                    <span className="font-semibold">Threshold:</span> {alarmData.comparisonOperator} {alarmData.threshold} in {alarmData.period} minute{alarmData.period !== 1 ? 's' : ''}
                  </div>
                  <div className="mb-2">
                    <span className="font-semibold">Status:</span> {alarmData.reason}
                  </div>
                  <div>
                    <span className="font-semibold">Triggered:</span> {new Date(alarmData.updatedAt).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="text-right">
          <div className={`text-5xl font-bold font-mono ${resolutionTime !== null ? 'text-emerald-600' : 'text-red-600'}`}>
            {resolutionTime !== null 
              ? formatTime(resolutionTime)
              : formatTime(elapsedTime)
            }
          </div>
          <p className={`text-sm mt-1 ${resolutionTime !== null ? 'text-emerald-600 font-semibold' : 'text-red-600'}`}>
            {resolutionTime !== null ? '✓ Resolution Time' : 'Time to Resolution'}
          </p>
        </div>
      </div>
      
      {/* Stop Timer Button */}
      {isTimerRunning && (
        <div className="flex justify-center">
          <button
            onClick={onRootCauseFound}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-all duration-200 hover:-translate-y-0.5 shadow-md hover:shadow-lg"
          >
            🎯 Stop Timer
          </button>
        </div>
      )}
      
      {/* Resolution Message */}
      {resolutionTime !== null && (
        <div className="mt-4 text-center">
          <p className="text-emerald-700 font-semibold text-lg">
            ✓ Root cause identified in {formatTime(resolutionTime)}
          </p>
        </div>
      )}
    </div>
  );
}
