// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// AWS Amplify configuration
import { Amplify } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { amplifyConfig } from './aws-config';
import App from './App';

// Configure Amplify
Amplify.configure(amplifyConfig as any);

export default function AuthenticatedApp() {
  return (
    <Authenticator
      loginMechanisms={['email']}
      signUpAttributes={['email']}
      components={{
        SignIn: {
          Header() {
            return (
              <div style={{ padding: '20px', textAlign: 'center' }}>
                <h2>AWS DevOps Agent Demo</h2>
                <p style={{ color: '#666', marginTop: '8px' }}>
                  Sign in to access the demo
                </p>
              </div>
            );
          },

        },
      }}
    >
      {({ signOut, user }) => (
        <div>
          {/* User info bar */}
          <div style={{
            background: '#f5f5f5',
            padding: '10px 20px',
            borderBottom: '1px solid #ddd',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <strong>AWS DevOps Agent Demo</strong>
              <span style={{ marginLeft: '20px', color: '#666' }}>
                Logged in as: {user?.signInDetails?.loginId || user?.username}
              </span>
            </div>
            <button
              onClick={signOut}
              style={{
                padding: '8px 16px',
                background: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Sign Out
            </button>
          </div>
          
          {/* Main app */}
          <App />
        </div>
      )}
    </Authenticator>
  );
}
