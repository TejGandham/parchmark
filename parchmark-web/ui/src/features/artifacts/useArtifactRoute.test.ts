import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  artifactPath,
  parseArtifactPath,
  resetArtifactRoute,
  useArtifactRoute,
} from "./useArtifactRoute";

describe("artifact route paths", () => {
  it("parses the list, an artifact id and non-artifact paths", () => {
    expect(parseArtifactPath("/artifacts")).toEqual({ artifactId: null });
    expect(parseArtifactPath("/artifacts/")).toEqual({ artifactId: null });
    expect(parseArtifactPath("/artifacts/42")).toEqual({ artifactId: 42 });
    expect(parseArtifactPath("/artifacts/nope")).toEqual({ artifactId: null });
    expect(parseArtifactPath("/")).toBeNull();
    expect(parseArtifactPath("/artifactsx")).toBeNull();
    expect(parseArtifactPath("/api/artifacts")).toBeNull();
  });

  it("formats a location as a path", () => {
    expect(artifactPath(null)).toBe("/");
    expect(artifactPath({ artifactId: null })).toBe("/artifacts");
    expect(artifactPath({ artifactId: 7 })).toBe("/artifacts/7");
  });
});

describe("useArtifactRoute", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    resetArtifactRoute();
  });

  afterEach(() => {
    window.history.replaceState(null, "", "/");
    resetArtifactRoute();
  });

  it("pushes a history entry per navigation and replaces on request", () => {
    const { location, go } = useArtifactRoute();
    const startLength = window.history.length;

    go({ artifactId: null });
    expect(window.location.pathname).toBe("/artifacts");
    expect(location.value).toEqual({ artifactId: null });

    go({ artifactId: 3 });
    expect(window.location.pathname).toBe("/artifacts/3");
    expect(window.history.length).toBe(startLength + 2);

    go({ artifactId: null }, { replace: true });
    expect(window.location.pathname).toBe("/artifacts");
    expect(window.history.length).toBe(startLength + 2);

    go(null);
    expect(window.location.pathname).toBe("/");
    expect(location.value).toBeNull();
  });

  it("does not push a duplicate entry for the current path", () => {
    const { go } = useArtifactRoute();
    go({ artifactId: null });
    const length = window.history.length;

    go({ artifactId: null });

    expect(window.history.length).toBe(length);
  });

  it("follows the address on popstate", () => {
    const { location } = useArtifactRoute();

    window.history.pushState(null, "", "/artifacts/5");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(location.value).toEqual({ artifactId: 5 });

    window.history.pushState(null, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(location.value).toBeNull();
  });

  it("reads the address at reset and canonicalizes a malformed artifact path", () => {
    window.history.replaceState(null, "", "/artifacts/not-a-number");
    resetArtifactRoute();

    const { location } = useArtifactRoute();

    expect(location.value).toEqual({ artifactId: null });
    expect(window.location.pathname).toBe("/artifacts");
  });
});
