import { readonly, ref, type DeepReadonly, type Ref } from "vue";

/**
 * Where the Artifacts view stands in the address bar: `null` when it is not
 * open, `{ artifactId: null }` for the list, `{ artifactId: n }` for one
 * artifact. Only the Artifacts view has URLs (`/artifacts`, `/artifacts/<id>`);
 * every other screen lives at `/`. Production nginx falls back to index.html
 * for unknown paths, so these deep paths survive a reload.
 */
export type ArtifactLocation = { artifactId: number | null } | null;

const ARTIFACTS_PATH = "/artifacts";
const ARTIFACT_PATH = /^\/artifacts(?:\/([^/]*))?\/?$/;

export function parseArtifactPath(pathname: string): ArtifactLocation {
  const match = ARTIFACT_PATH.exec(pathname);
  if (!match) return null;
  const segment = match[1] ?? "";
  return { artifactId: /^\d+$/.test(segment) ? Number(segment) : null };
}

export function artifactPath(location: ArtifactLocation): string {
  if (location === null) return "/";
  return location.artifactId === null
    ? ARTIFACTS_PATH
    : `${ARTIFACTS_PATH}/${location.artifactId}`;
}

// One shared location for the whole app, so the shell and the Artifacts view
// read and change the same address.
const current = ref<ArtifactLocation>(null);

/**
 * Re-read the address bar into the shared location, rewriting a malformed
 * Artifacts path (e.g. `/artifacts/abc`) to its canonical form in place.
 */
export function resetArtifactRoute(): void {
  const { pathname } = window.location;
  const location = parseArtifactPath(pathname);
  if (location !== null && artifactPath(location) !== pathname) {
    window.history.replaceState(
      window.history.state,
      "",
      artifactPath(location),
    );
  }
  current.value = location;
}

resetArtifactRoute();
window.addEventListener("popstate", resetArtifactRoute);

export function useArtifactRoute(): {
  location: DeepReadonly<Ref<ArtifactLocation>>;
  go: (next: ArtifactLocation, options?: { replace?: boolean }) => void;
} {
  function go(next: ArtifactLocation, { replace = false } = {}) {
    const path = artifactPath(next);
    if (path !== window.location.pathname) {
      if (replace) {
        window.history.replaceState(null, "", path);
      } else {
        window.history.pushState(null, "", path);
      }
    }
    current.value = next;
  }

  return { location: readonly(current), go };
}
