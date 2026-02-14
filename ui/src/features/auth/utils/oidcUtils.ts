/**
 * OIDC utilities for handling Authelia SSO flows
 */

import { User, UserManager, WebStorageStateStore } from 'oidc-client-ts';
import { OIDC_CONFIG } from '../../../config/oidc';

/**
 * Discriminated union for OIDC operations that can fail silently
 * Allows callers to distinguish between "no user" and "error occurred"
 */
export type OIDCResult<T> =
  | { success: true; data: T }
  | { success: false; error: Error };

// Initialize OIDC UserManager
const userManager = new UserManager({
  ...OIDC_CONFIG,
  userStore: new WebStorageStateStore({ store: window.sessionStorage }),
});

/**
 * Start OIDC login flow
 * Redirects to Authelia authorization endpoint
 */
export const startOIDCLogin = async () => {
  try {
    await userManager.signinRedirect();
  } catch (error) {
    const errorDetails =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : String(error);
    console.error(`OIDC login failed: ${errorDetails}`, { original: error });
    throw error;
  }
};

/**
 * Handle OIDC callback from Authelia
 * Exchanges authorization code for tokens
 */
export const handleOIDCCallback = async () => {
  try {
    const user = await userManager.signinRedirectCallback();
    return user;
  } catch (error) {
    const errorDetails =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : String(error);
    console.error(`OIDC callback failed: ${errorDetails}`, { original: error });
    throw error;
  }
};

/**
 * Get current OIDC user
 * Returns discriminated result to distinguish "no user" from "error"
 */
export const getOIDCUser = async (): Promise<OIDCResult<User | null>> => {
  try {
    const user = await userManager.getUser();
    return { success: true, data: user };
  } catch (error) {
    const errorObj = error instanceof Error ? error : new Error(String(error));
    console.error(`Failed to get OIDC user: ${errorObj.message}`, {
      original: error,
    });
    return { success: false, error: errorObj };
  }
};

/**
 * Renew OIDC tokens silently
 * Returns discriminated result to distinguish "renewal failed" from "error"
 */
export const renewOIDCToken = async (): Promise<OIDCResult<User | null>> => {
  try {
    const user = await userManager.signinSilent();
    return { success: true, data: user };
  } catch (error) {
    const errorObj = error instanceof Error ? error : new Error(String(error));
    console.error(`OIDC token renewal failed: ${errorObj.message}`, {
      original: error,
    });
    return { success: false, error: errorObj };
  }
};

/**
 * Logout from OIDC (Authelia)
 * Redirects to the OIDC provider's end_session endpoint to terminate the
 * provider-side session, then redirects back to post_logout_redirect_uri.
 *
 * When signoutRedirect fails (e.g., provider doesn't advertise
 * end_session_endpoint — Authelia omits it), falls back to the provider's
 * native logout page: `{authority}/logout?rd={post_logout_redirect_uri}`.
 * This navigates the browser away, so the returned promise never resolves.
 */
export const logoutOIDC = async () => {
  try {
    await userManager.signoutRedirect();
  } catch (error) {
    try {
      await userManager.removeUser();
    } catch {
      /* best-effort local cleanup */
    }

    const errorDetails =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : String(error);
    console.warn(
      `OIDC signoutRedirect unavailable, using native provider logout: ${errorDetails}`
    );

    // Authelia omits end_session_endpoint from OIDC discovery —
    // redirect to its native /logout page which accepts `rd` for post-logout redirect.
    const postLogoutUri = OIDC_CONFIG.post_logout_redirect_uri;
    const logoutUrl = `${OIDC_CONFIG.authority}/logout?rd=${encodeURIComponent(postLogoutUri)}`;
    window.location.assign(logoutUrl);

    // Page is navigating away — never resolve so caller doesn't run teardown code.
    return new Promise<never>(() => {});
  }
};

export default userManager;
