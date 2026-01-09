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
 * Clears local OIDC session. Does not redirect to IDP - Authelia session remains active.
 * User will need to visit https://auth.engen.tech/logout manually for full IDP logout.
 */
export const logoutOIDC = async () => {
  try {
    // Clear the local OIDC session
    await userManager.removeUser();
    // Note: Authelia session remains active. Logging back in will be seamless
    // if the Authelia session hasn't expired.
  } catch (error) {
    const errorDetails =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : String(error);
    console.error(`OIDC logout failed: ${errorDetails}`, { original: error });
    throw error;
  }
};

export default userManager;
