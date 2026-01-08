/**
 * OIDC utilities for handling Authelia SSO flows
 */

import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import { OIDC_CONFIG } from "../../../config/oidc";

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
    const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
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
    const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`OIDC callback failed: ${errorDetails}`, { original: error });
    throw error;
  }
};

/**
 * Get current OIDC user
 */
export const getOIDCUser = async () => {
  try {
    return await userManager.getUser();
  } catch (error) {
    const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`Failed to get OIDC user: ${errorDetails}`, { original: error });
    return null;
  }
};

/**
 * Renew OIDC tokens silently
 */
export const renewOIDCToken = async () => {
  try {
    const user = await userManager.signinSilent();
    return user;
  } catch (error) {
    const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`OIDC token renewal failed: ${errorDetails}`, { original: error });
    return null;
  }
};

/**
 * Logout from OIDC (Authelia)
 */
export const logoutOIDC = async () => {
  try {
    await userManager.signoutRedirect();
  } catch (error) {
    const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`OIDC logout failed: ${errorDetails}`, { original: error });
    throw error;
  }
};

export default userManager;
