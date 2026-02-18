export const APP_VERSION = __APP_VERSION__;
export const GIT_SHA = __GIT_SHA__;
export const BUILD_DATE = __BUILD_DATE__;

export const getVersionInfo = () => ({
  version: APP_VERSION,
  gitSha: GIT_SHA,
  buildDate: BUILD_DATE,
});

export const getVersionString = (): string => {
  const sha = GIT_SHA.length > 7 ? GIT_SHA.slice(0, 7) : GIT_SHA;
  return `${APP_VERSION} (${sha})`;
};
