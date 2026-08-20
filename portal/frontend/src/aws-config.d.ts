interface RuntimeConfig {
  userPoolId: string;
  userPoolClientId: string;
  identityPoolId: string;
  apiUrl: string;
}

declare global {
  interface Window {
    __config: RuntimeConfig;
  }
}

export const amplifyConfig: {
  Auth: {
    Cognito: {
      userPoolId: string;
      userPoolClientId: string;
      identityPoolId: string;
      loginWith: { email: boolean };
      signUpVerificationMethod: string;
      userAttributes: { email: { required: boolean } };
      allowGuestAccess: boolean;
      passwordFormat: {
        minLength: number;
        requireLowercase: boolean;
        requireUppercase: boolean;
        requireNumbers: boolean;
        requireSpecialCharacters: boolean;
      };
    };
  };
};
