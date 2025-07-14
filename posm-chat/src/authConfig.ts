// src/authConfig.ts
const getEnv = (viteKey: keyof ImportMetaEnv): string => {
  return import.meta.env[viteKey] || '';
};

export const oidcConfig = {
  // The authoritative address of Azure AD (fixed format)
  authority: `https://login.microsoftonline.com/${getEnv('VITE_AZURE_TENANT_ID')}`,
  // The client ID of the application registration
  client_id: getEnv('VITE_AZURE_CLIENT_ID'),
  // Redirect URI (must be consistent with Azure portal configuration)
  redirect_uri: getEnv('VITE_REDIRECT_URI'),
  // Redirect the address after logging out
  post_logout_redirect_uri: getEnv('window.VITE_HOME_URI'),
  // The scope of the requested permission
  scope: "openid profile email",
  // Response type (authorized bitstream)
  response_type: "code",
  // Automatically refresh the token
  automaticSilentRenew: true,
}; 

// declare global {
//   interface Window {
//     VITE_AZURE_TENANT_ID: string;
//     VITE_AZURE_CLIENT_ID: string;
//     VITE_REDIRECT_URI: string;
//     VITE_HOME_URI: string;
//   }
// }

// export const oidcConfig = {
//   // The authoritative address of Azure AD (fixed format)
//   authority: `https://login.microsoftonline.com/${window.VITE_AZURE_TENANT_ID}`,
//   // The client ID of the application registration
//   client_id: window.VITE_AZURE_CLIENT_ID,
//   // Redirect URI (must be consistent with Azure portal configuration)
//   redirect_uri: window.VITE_REDIRECT_URI,
//   // Redirect the address after logging out
//   post_logout_redirect_uri: window.VITE_HOME_URI,
//   // The scope of the requested permission
//   scope: "openid profile email",
//   // Response type (authorized bitstream)
//   response_type: "code",
//   // Automatically refresh the token
//   automaticSilentRenew: true,
// }; 