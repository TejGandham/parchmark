/**
 * OIDC Configuration for Authelia SSO
 *
 * ParchMark is a public client (browser SPA) - uses PKCE, no client secret.
 * Authelia must be configured with: public: true
 */

const OIDC_ISSUER_URL =
  import.meta.env.VITE_OIDC_ISSUER_URL || 'https://auth.engen.tech';
const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'parchmark';
const OIDC_REDIRECT_URI =
  import.meta.env.VITE_OIDC_REDIRECT_URI ||
  (typeof window !== 'undefined'
    ? `${window.location.origin}/oidc/callback`
    : 'http://localhost:5173/oidc/callback');
const OIDC_LOGOUT_REDIRECT_URI =
  import.meta.env.VITE_OIDC_LOGOUT_REDIRECT_URI ||
  (typeof window !== 'undefined'
    ? `${window.location.origin}/login`
    : 'http://localhost:5173/login');

export const OIDC_CONFIG = {
  authority: OIDC_ISSUER_URL,
  client_id: OIDC_CLIENT_ID,
  redirect_uri: OIDC_REDIRECT_URI,
  post_logout_redirect_uri: OIDC_LOGOUT_REDIRECT_URI,
  response_type: 'code',
  scope: 'openid profile email',
  response_mode: 'query',
  // PKCE for public client (browser SPA)
  code_challenge_method: 'S256',
};

export const OIDC_ENDPOINTS = {
  authorization: `${OIDC_ISSUER_URL}/authorization`,
  token: `${OIDC_ISSUER_URL}/token`,
  userinfo: `${OIDC_ISSUER_URL}/userinfo`,
  endSession: `${OIDC_ISSUER_URL}/end_session`,
};
