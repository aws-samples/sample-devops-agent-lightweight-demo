
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// ArchitectureDiagram component - Visual representation of the demo architecture
// Shows the flow: User -> Frontend -> Lambda -> DynamoDB
// Highlights the two error points for business audience

export function ArchitectureDiagram() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <h2 className="text-2xl font-medium mb-4 text-slate-800">Technical Architecture</h2>
      
      <svg viewBox="0 0 800 250" className="w-full h-auto">
        {/* User */}
        <g>
          <text x="50" y="155" textAnchor="middle" fontSize="40">👤</text>
          <text x="50" y="195" textAnchor="middle" fontSize="14" fontWeight="normal" fill="#64748B">User</text>
        </g>

        {/* Arrow to Frontend */}
        <line x1="80" y1="150" x2="130" y2="150" stroke="#94A3B8" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
        
        {/* Frontend */}
        <g>
          <rect x="130" y="120" width="100" height="60" rx="5" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
          <text x="180" y="155" textAnchor="middle" fill="#334155" fontSize="15" fontWeight="500">Frontend</text>
          <text x="180" y="205" textAnchor="middle" fontSize="11" fill="#94A3B8" fontWeight="300">React App</text>
        </g>

        {/* Arrow to Lambda */}
        <line x1="230" y1="150" x2="280" y2="150" stroke="#94A3B8" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
        
        {/* Lambda Function */}
        <g>
          <rect x="280" y="100" width="140" height="100" rx="5" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
          <text x="350" y="130" textAnchor="middle" fill="#334155" fontSize="15" fontWeight="500">Lambda</text>
          <text x="350" y="150" textAnchor="middle" fill="#94A3B8" fontSize="11" fontWeight="300">Order Processing</text>
          
          {/* Error: Code Bug in Lambda */}
          <rect x="290" y="160" width="120" height="35" rx="3" fill="#991B1B" stroke="#7F1D1D" strokeWidth="1.5" />
          <text x="350" y="175" textAnchor="middle" fill="white" fontSize="10" fontWeight="500">⚠️ Code Bug</text>
          <text x="350" y="188" textAnchor="middle" fill="#FCA5A5" fontSize="9" fontWeight="300">update_item() on new orders</text>
        </g>

        {/* Arrow to DynamoDB */}
        <line x1="420" y1="150" x2="470" y2="150" stroke="#94A3B8" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
        
        {/* DynamoDB */}
        <g>
          <rect x="470" y="120" width="140" height="60" rx="5" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
          <text x="540" y="155" textAnchor="middle" fill="#334155" fontSize="15" fontWeight="500">DynamoDB</text>
          <text x="540" y="205" textAnchor="middle" fill="#94A3B8" fontSize="11" fontWeight="300">demo-user-data</text>
        </g>

        {/* CloudWatch Alarm - Centered above Lambda */}
        <g>
          <rect x="290" y="20" width="120" height="50" rx="5" fill="#F59E0B" stroke="#D97706" strokeWidth="1.5" />
          <text x="350" y="42" textAnchor="middle" fill="white" fontSize="13" fontWeight="500">🚨 CloudWatch</text>
          <text x="350" y="58" textAnchor="middle" fill="#FEF3C7" fontSize="11" fontWeight="300">Alarm</text>
        </g>

        {/* Monitoring line from Lambda to Alarm - Vertical */}
        <line x1="350" y1="100" x2="350" y2="70" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="5,5" />

        {/* Arrow marker definition */}
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#94A3B8" />
          </marker>
        </defs>

        {/* Legend */}
        <g transform="translate(630, 20)">
          <text x="0" y="0" fontSize="13" fontWeight="500" fill="#334155">Legend:</text>
          <rect x="0" y="8" width="20" height="12" fill="#991B1B" stroke="#7F1D1D" strokeWidth="1" />
          <text x="25" y="18" fontSize="11" fontWeight="300" fill="#64748B">Code Bug</text>
          
          <line x1="0" y1="32" x2="20" y2="32" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="5,5" />
          <text x="25" y="37" fontSize="11" fontWeight="300" fill="#64748B">Monitoring</text>
        </g>
      </svg>

      {/* Error Description */}
      <div className="mt-6">
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <h3 className="font-semibold text-red-800 mb-2">Root Cause: Code Logic Error</h3>
          <p className="text-sm text-red-700 mb-2">
            Lambda function uses <code className="bg-red-100 px-1 rounded">update_item()</code> with 
            <code className="bg-red-100 px-1 rounded">attribute_exists()</code> condition on new orders.
          </p>
          <p className="text-sm text-red-700">
            <strong>Issue:</strong> Each order gets a unique ID that doesn't exist in DynamoDB yet, 
            causing <code className="bg-red-100 px-1 rounded">ConditionalCheckFailedException</code> every time.
          </p>
          <p className="text-sm text-red-700 mt-2">
            <strong>Fix:</strong> Change to <code className="bg-red-100 px-1 rounded">put_item()</code> for new orders.
          </p>
        </div>
      </div>
    </div>
  );
}
