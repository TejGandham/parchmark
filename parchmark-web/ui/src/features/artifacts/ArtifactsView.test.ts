import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import MarkdownProse from "@/features/notes/MarkdownProse.vue";
import { renderMarkdownBody } from "@/features/notes/markdownRender";
import { ApiError } from "@/services/http";
import type {
  ArtifactContentType,
  ArtifactDTO,
  ArtifactVisibility,
} from "@/services/artifacts";

import ArtifactsView from "./ArtifactsView.vue";

enableAutoUnmount(afterEach);

const api = vi.hoisted(() => ({
  listArtifacts: vi.fn(),
  createViewLink: vi.fn(),
  getArtifactContent: vi.fn(),
  setArtifactVisibility: vi.fn(),
  deleteArtifact: vi.fn(),
}));
vi.mock("@/services/artifacts", () => api);

// Wrap the real sanitizer in a spy so the markdown path is proven to go
// through renderMarkdownBody (the DOMPurify path) and nothing else.
vi.mock("@/features/notes/markdownRender", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/features/notes/markdownRender")>();
  return { ...actual, renderMarkdownBody: vi.fn(actual.renderMarkdownBody) };
});

// A content origin on a host other than the page's (jsdom runs on localhost).
const CONTENT_ORIGIN = "https://content.example.net";

function makeArtifact(
  id: number,
  contentType: ArtifactContentType,
  visibility: ArtifactVisibility,
  title = `Artifact ${id}`,
): ArtifactDTO {
  return {
    id,
    slug: `slug-${id}`,
    title,
    visibility,
    created_at: "2026-10-01T10:00:00Z",
    current_version: {
      id: id * 10,
      version: 3,
      content_type: contentType,
      created_at: "2026-10-02T10:00:00Z",
    },
    share_url: `${CONTENT_ORIGIN}/a/slug-${id}`,
  };
}

let mintCount = 0;
function mintedUrl(id: number, n: number): string {
  return `${CONTENT_ORIGIN}/a/slug-${id}?exp=1&sig=mint-${n}`;
}

async function mountWith(artifacts: ArtifactDTO[]) {
  api.listArtifacts.mockResolvedValue(artifacts);
  const wrapper = mount(ArtifactsView);
  await flushPromises();
  return wrapper;
}

async function openCard(
  wrapper: Awaited<ReturnType<typeof mountWith>>,
  title: string,
) {
  const card = wrapper
    .findAll(".artifact-card")
    .find((candidate) => candidate.text().includes(title));
  expect(card).toBeTruthy();
  await card!.trigger("click");
  await flushPromises();
}

function assertNoSrcdocOrBlob(root: Element) {
  expect(root.querySelectorAll("[srcdoc]")).toHaveLength(0);
  for (const frame of Array.from(root.querySelectorAll("iframe"))) {
    expect(frame.getAttribute("src") ?? "").not.toMatch(/^blob:/);
  }
}

describe("ArtifactsView", () => {
  beforeEach(() => {
    mintCount = 0;
    for (const fn of Object.values(api)) fn.mockReset();
    vi.mocked(renderMarkdownBody).mockClear();
    api.createViewLink.mockImplementation((id: number) => {
      mintCount += 1;
      return Promise.resolve({
        url: mintedUrl(id, mintCount),
        expires_at: "2026-10-18T12:00:00Z",
      });
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("gallery", () => {
    it("lists the artifacts that the list endpoint returns", async () => {
      const wrapper = await mountWith([
        makeArtifact(1, "html", "private", "Chart"),
        makeArtifact(2, "markdown", "unlisted", "Notes"),
      ]);

      expect(api.listArtifacts).toHaveBeenCalledTimes(1);
      const cards = wrapper.findAll(".artifact-card");
      expect(cards).toHaveLength(2);
      expect(cards[0].text()).toContain("Chart");
      expect(cards[0].text()).toContain("html");
      expect(cards[0].text()).toContain("private");
      expect(cards[0].text()).toContain("v3");
      expect(cards[1].text()).toContain("Notes");
      expect(cards[1].text()).toContain("markdown");
      expect(cards[1].text()).toContain("unlisted");
    });

    it("shows an empty state when there are no artifacts", async () => {
      const wrapper = await mountWith([]);

      expect(wrapper.findAll(".artifact-card")).toHaveLength(0);
      expect(wrapper.text()).toContain("No artifacts yet");
    });

    it("shows the list error and retries", async () => {
      api.listArtifacts.mockRejectedValueOnce(new ApiError(500, "list failed"));
      const wrapper = mount(ArtifactsView);
      await flushPromises();

      expect(wrapper.get('[role="alert"]').text()).toContain("list failed");

      api.listArtifacts.mockResolvedValueOnce([
        makeArtifact(1, "svg", "private"),
      ]);
      await wrapper.get(".artifacts-retry").trigger("click");
      await flushPromises();

      expect(wrapper.findAll(".artifact-card")).toHaveLength(1);
    });
  });

  it("shows a generic message for a non-API failure", async () => {
    api.listArtifacts.mockRejectedValueOnce(new TypeError("network down"));
    const wrapper = mount(ArtifactsView);
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Something went wrong",
    );
  });

  describe("framed viewer", () => {
    const cases: Array<[ArtifactContentType, ArtifactVisibility]> = [
      ["html", "private"],
      ["html", "unlisted"],
      ["svg", "private"],
      ["svg", "unlisted"],
    ];

    it.each(cases)(
      "frames a %s artifact (%s) through the minted link",
      async (contentType, visibility) => {
        const wrapper = await mountWith([
          makeArtifact(5, contentType, visibility, "Framed"),
        ]);

        await openCard(wrapper, "Framed");

        expect(api.createViewLink).toHaveBeenCalledTimes(1);
        expect(api.createViewLink).toHaveBeenCalledWith(5);
        expect(api.getArtifactContent).not.toHaveBeenCalled();
        const frames = wrapper.findAll("iframe");
        expect(frames).toHaveLength(1);
        const frame = frames[0].element;
        expect(frame.getAttribute("src")).toBe(mintedUrl(5, 1));
        expect(frame.getAttribute("sandbox")).toBe("allow-scripts");
        expect(frame.getAttribute("referrerpolicy")).toBe("no-referrer");
        assertNoSrcdocOrBlob(wrapper.element);
      },
    );

    it("renders no iframe before the mint resolves", async () => {
      let resolveMint!: (value: { url: string; expires_at: string }) => void;
      api.createViewLink.mockReturnValueOnce(
        new Promise((resolve) => {
          resolveMint = resolve;
        }),
      );
      const wrapper = await mountWith([makeArtifact(5, "html", "private")]);

      await openCard(wrapper, "Artifact 5");
      expect(wrapper.find("iframe").exists()).toBe(false);

      resolveMint({ url: mintedUrl(5, 9), expires_at: "x" });
      await flushPromises();
      expect(wrapper.get("iframe").attributes("src")).toBe(mintedUrl(5, 9));
    });

    it("shows an error and no iframe when the mint fails", async () => {
      api.createViewLink.mockRejectedValueOnce(
        new ApiError(500, "mint failed"),
      );
      const wrapper = await mountWith([makeArtifact(5, "svg", "unlisted")]);

      await openCard(wrapper, "Artifact 5");

      expect(wrapper.find("iframe").exists()).toBe(false);
      expect(wrapper.get('[role="alert"]').text()).toContain("mint failed");
    });

    it("mints a fresh link each time the same artifact is reopened", async () => {
      const wrapper = await mountWith([makeArtifact(5, "html", "private")]);

      await openCard(wrapper, "Artifact 5");
      expect(wrapper.get("iframe").attributes("src")).toBe(mintedUrl(5, 1));

      await wrapper.get(".artifact-back").trigger("click");
      await flushPromises();
      expect(wrapper.find("iframe").exists()).toBe(false);

      await openCard(wrapper, "Artifact 5");
      expect(api.createViewLink).toHaveBeenCalledTimes(2);
      expect(wrapper.get("iframe").attributes("src")).toBe(mintedUrl(5, 2));
      assertNoSrcdocOrBlob(wrapper.element);
    });
  });

  describe("markdown viewer", () => {
    it("renders content through renderMarkdownBody with no iframe", async () => {
      api.getArtifactContent.mockResolvedValue({
        version: 3,
        content_type: "markdown",
        content: "Intro\n\n## Section\n\n<img src=x onerror=alert(1)>",
      });
      const wrapper = await mountWith([
        makeArtifact(8, "markdown", "unlisted", "Doc"),
      ]);

      await openCard(wrapper, "Doc");

      expect(api.getArtifactContent).toHaveBeenCalledWith(8);
      expect(api.createViewLink).not.toHaveBeenCalled();
      expect(wrapper.find("iframe").exists()).toBe(false);
      expect(wrapper.getComponent(MarkdownProse).props("markdown")).toBe(
        "Intro\n\n## Section\n\n<img src=x onerror=alert(1)>",
      );
      expect(renderMarkdownBody).toHaveBeenCalledWith(
        "Intro\n\n## Section\n\n<img src=x onerror=alert(1)>",
      );
      expect(wrapper.get(".prose h2").text()).toBe("Section");
      expect(wrapper.find(".prose img").exists()).toBe(true);
      expect(wrapper.find(".prose [onerror]").exists()).toBe(false);
      assertNoSrcdocOrBlob(wrapper.element);
    });

    it("shows an error when the content request fails", async () => {
      api.getArtifactContent.mockRejectedValueOnce(
        new ApiError(404, "Artifact not found"),
      );
      const wrapper = await mountWith([makeArtifact(8, "markdown", "private")]);

      await openCard(wrapper, "Artifact 8");

      expect(wrapper.get('[role="alert"]').text()).toContain(
        "Artifact not found",
      );
      expect(wrapper.findComponent(MarkdownProse).exists()).toBe(false);
    });
  });

  describe("controls", () => {
    it("disables copy link while private and copies share_url exactly once unlisted", async () => {
      const writeText = vi.fn().mockResolvedValue(undefined);
      vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
      const privateArtifact = makeArtifact(3, "html", "private");
      const unlisted = { ...privateArtifact, visibility: "unlisted" as const };
      api.setArtifactVisibility.mockResolvedValue(unlisted);
      const wrapper = await mountWith([privateArtifact]);
      await openCard(wrapper, "Artifact 3");

      const copy = wrapper.get(".artifact-copy");
      expect(copy.attributes("disabled")).toBeDefined();
      await copy.trigger("click");
      expect(writeText).not.toHaveBeenCalled();

      await wrapper.get('[data-visibility="unlisted"]').trigger("click");
      await flushPromises();

      expect(wrapper.get(".artifact-copy").attributes("disabled")).toBe(
        undefined,
      );
      await wrapper.get(".artifact-copy").trigger("click");
      await flushPromises();

      expect(new URL(unlisted.share_url).host).not.toBe(window.location.host);
      expect(writeText).toHaveBeenCalledTimes(1);
      expect(writeText).toHaveBeenCalledWith(unlisted.share_url);
      expect(wrapper.text()).toContain("Link copied");
    });

    it("shows a copy error when the clipboard rejects", async () => {
      const writeText = vi.fn().mockRejectedValue(new Error("denied"));
      vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
      const wrapper = await mountWith([makeArtifact(3, "svg", "unlisted")]);
      await openCard(wrapper, "Artifact 3");

      await wrapper.get(".artifact-copy").trigger("click");
      await flushPromises();

      expect(wrapper.get('[role="alert"]').text()).toContain(
        "Could not copy the link",
      );
    });

    it("calls the visibility endpoint with the chosen value and shows the returned state", async () => {
      const unlisted = makeArtifact(3, "html", "unlisted", "Toggle");
      api.setArtifactVisibility
        .mockResolvedValueOnce({ ...unlisted, visibility: "private" })
        .mockResolvedValueOnce(unlisted);
      const wrapper = await mountWith([unlisted]);
      await openCard(wrapper, "Toggle");

      expect(
        wrapper.get('[data-visibility="unlisted"]').attributes("aria-pressed"),
      ).toBe("true");

      await wrapper.get('[data-visibility="private"]').trigger("click");
      await flushPromises();
      expect(api.setArtifactVisibility).toHaveBeenLastCalledWith(3, "private");
      expect(
        wrapper.get('[data-visibility="private"]').attributes("aria-pressed"),
      ).toBe("true");
      expect(
        wrapper.get(".artifact-copy").attributes("disabled"),
      ).toBeDefined();

      await wrapper.get('[data-visibility="unlisted"]').trigger("click");
      await flushPromises();
      expect(api.setArtifactVisibility).toHaveBeenLastCalledWith(3, "unlisted");
      expect(api.setArtifactVisibility).toHaveBeenCalledTimes(2);

      // The gallery reflects the state the server returned.
      await wrapper.get(".artifact-back").trigger("click");
      expect(wrapper.get(".artifact-card").text()).toContain("unlisted");
    });

    it("does not call the endpoint when the current visibility is chosen again", async () => {
      const wrapper = await mountWith([makeArtifact(3, "html", "private")]);
      await openCard(wrapper, "Artifact 3");

      await wrapper.get('[data-visibility="private"]').trigger("click");
      await flushPromises();

      expect(api.setArtifactVisibility).not.toHaveBeenCalled();
    });

    it("keeps the old state and shows an error when the visibility change fails", async () => {
      api.setArtifactVisibility.mockRejectedValueOnce(
        new ApiError(500, "visibility failed"),
      );
      const wrapper = await mountWith([makeArtifact(3, "html", "private")]);
      await openCard(wrapper, "Artifact 3");

      await wrapper.get('[data-visibility="unlisted"]').trigger("click");
      await flushPromises();

      expect(wrapper.get('[role="alert"]').text()).toContain(
        "visibility failed",
      );
      expect(
        wrapper.get('[data-visibility="private"]').attributes("aria-pressed"),
      ).toBe("true");
    });

    it("cancelling the delete confirmation calls nothing", async () => {
      const wrapper = await mountWith([makeArtifact(4, "html", "private")]);
      await openCard(wrapper, "Artifact 4");

      await wrapper.get(".artifact-delete").trigger("click");
      expect(api.deleteArtifact).not.toHaveBeenCalled();
      await wrapper.get(".artifact-delete-cancel").trigger("click");
      await flushPromises();

      expect(api.deleteArtifact).not.toHaveBeenCalled();
      expect(wrapper.find(".artifact-delete-confirm").exists()).toBe(false);
    });

    it("deletes only after confirmation and returns to the gallery without it", async () => {
      api.deleteArtifact.mockResolvedValue({
        message: "deleted",
        deleted_id: "4",
      });
      const wrapper = await mountWith([
        makeArtifact(4, "html", "private", "Doomed"),
        makeArtifact(6, "svg", "private", "Survivor"),
      ]);
      await openCard(wrapper, "Doomed");

      await wrapper.get(".artifact-delete").trigger("click");
      expect(api.deleteArtifact).not.toHaveBeenCalled();
      await wrapper.get(".artifact-delete-confirm").trigger("click");
      await flushPromises();

      expect(api.deleteArtifact).toHaveBeenCalledTimes(1);
      expect(api.deleteArtifact).toHaveBeenCalledWith(4);
      expect(wrapper.find("iframe").exists()).toBe(false);
      const cards = wrapper.findAll(".artifact-card");
      expect(cards).toHaveLength(1);
      expect(cards[0].text()).toContain("Survivor");
    });

    it("stays on the viewer with an error when delete fails", async () => {
      api.deleteArtifact.mockRejectedValueOnce(
        new ApiError(500, "delete failed"),
      );
      const wrapper = await mountWith([makeArtifact(4, "html", "private")]);
      await openCard(wrapper, "Artifact 4");

      await wrapper.get(".artifact-delete").trigger("click");
      await wrapper.get(".artifact-delete-confirm").trigger("click");
      await flushPromises();

      expect(wrapper.get('[role="alert"]').text()).toContain("delete failed");
      expect(wrapper.find(".artifact-back").exists()).toBe(true);
    });
  });
});
