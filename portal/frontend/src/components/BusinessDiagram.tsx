
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// BusinessDiagram component - Simple customer-focused flow diagram
// Shows: Customer → Order API → Database
// Uses business-friendly language without technical jargon

interface BusinessDiagramProps {
  isOperational: boolean;
}

export function BusinessDiagram({ isOperational }: BusinessDiagramProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <h2 className="text-2xl font-medium mb-4 text-slate-800">Customer Order Flow</h2>
      
      <svg viewBox="0 0 800 200" className="w-full h-auto">
        {/* Customer */}
        <g>
          <text x="80" y="105" textAnchor="middle" fontSize="40">👤</text>
          <text x="80" y="145" textAnchor="middle" fontSize="14" fontWeight="normal" fill="#64748B">Customer</text>
        </g>

        {/* Arrow to Order API */}
        <line x1="120" y1="100" x2="220" y2="100" stroke="#94A3B8" strokeWidth="2" markerEnd="url(#arrow-business)" />
        
        {/* Order API */}
        <g>
          <rect x="220" y="70" width="140" height="60" rx="8" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
          <text x="290" y="105" textAnchor="middle" fill="#334155" fontSize="16" fontWeight="500">Order API</text>
        </g>

        {/* Arrow to Database */}
        <line x1="360" y1="100" x2="460" y2="100" stroke="#94A3B8" strokeWidth="2" markerEnd="url(#arrow-business)" />
        
        {/* Database */}
        <g>
          <rect x="460" y="70" width="140" height="60" rx="8" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
          <text x="530" y="105" textAnchor="middle" fill="#334155" fontSize="16" fontWeight="500">Database</text>
        </g>

        {/* Status Indicator */}
        <g transform="translate(650, 70)">
          {isOperational ? (
            <>
              <circle cx="20" cy="20" r="12" fill="#10B981" opacity="0.2" />
              <circle cx="20" cy="20" r="6" fill="#10B981" />
              <text x="40" y="26" fontSize="14" fontWeight="500" fill="#059669">Operational</text>
            </>
          ) : (
            <>
              <circle cx="20" cy="20" r="12" fill="#EF4444" opacity="0.2" />
              <circle cx="20" cy="20" r="6" fill="#EF4444" />
              <text x="40" y="26" fontSize="14" fontWeight="500" fill="#DC2626">Orders Failing</text>
            </>
          )}
        </g>

        {/* Arrow marker definition */}
        <defs>
          <marker id="arrow-business" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#94A3B8" />
          </marker>
        </defs>
      </svg>

      {/* Status Message */}
      <div className="mt-6 text-center">
        {isOperational ? (
          <p className="text-emerald-700 font-medium">
            ✓ System Status: Orders Processing Successfully
          </p>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-semibold mb-1">⚠️ Customer Orders Cannot Be Processed</p>
            <p className="text-red-700 text-sm">System is in a degraded state - customer experience impacted</p>
          </div>
        )}
      </div>
    </div>
  );
}
