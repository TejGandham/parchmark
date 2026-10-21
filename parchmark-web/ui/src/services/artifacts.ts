import { request } from "./http";

export type ArtifactContentType = "html" | "markdown" | "svg";
export type ArtifactVisibility = "private" | "unlisted";

export interface ArtifactVersionDTO {
  id: number;
  version: number;
  content_type: ArtifactContentType;
  created_at: string;
}

export interface ArtifactDTO {
  id: number;
  slug: string;
  title: string;
  visibility: ArtifactVisibility;
  created_at: string;
  current_version: ArtifactVersionDTO;
  /**
   * The backend-built share link, `<content origin>/a/<slug>`. It serves the
   * content only while the artifact is unlisted. The UI relays it as-is and
   * never builds an artifact URL itself.
   */
  share_url: string;
}

/** A short-lived signed link to the artifact on the content origin. */
export interface ViewLinkDTO {
  url: string;
  expires_at: string;
}

export interface ArtifactContentDTO {
  version: number;
  content_type: ArtifactContentType;
  content: string;
}

export interface DeleteArtifactResponse {
  message: string;
  deleted_id: string;
}

/** List the signed-in user's artifacts, newest first. */
export function listArtifacts(): Promise<ArtifactDTO[]> {
  return request<ArtifactDTO[]>("/artifacts", { method: "GET" });
}

/** Mint a fresh signed view link for one of the user's artifacts. */
export function createViewLink(id: number): Promise<ViewLinkDTO> {
  return request<ViewLinkDTO>(`/artifacts/${id}/view-link`, {
    method: "POST",
  });
}

/** Read the raw content of an artifact's current version. */
export function getArtifactContent(id: number): Promise<ArtifactContentDTO> {
  return request<ArtifactContentDTO>(`/artifacts/${id}/content`, {
    method: "GET",
  });
}

/** Set who can read an artifact; resolves to the updated artifact. */
export function setArtifactVisibility(
  id: number,
  visibility: ArtifactVisibility,
): Promise<ArtifactDTO> {
  return request<ArtifactDTO>(`/artifacts/${id}/visibility`, {
    method: "POST",
    body: { visibility },
  });
}

/** Delete an artifact together with all of its versions. */
export function deleteArtifact(id: number): Promise<DeleteArtifactResponse> {
  return request<DeleteArtifactResponse>(`/artifacts/${id}`, {
    method: "DELETE",
  });
}
