import { request } from "./http";

/**
 * Shape of a note as returned by the backend `NoteResponse` schema
 * (`backend/app/schemas/schemas.py:73`). All timestamp fields are ISO-8601
 * strings. Tags are already normalized and deduplicated by the backend.
 *
 * The `title` field is kept on the wire contract even though the frontend
 * currently derives titles client-side via `extractTitle`. Carrying it
 * preserves the option to consume the backend title later without another
 * client change.
 */
export interface NoteDTO {
  id: string;
  title: string;
  content: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateNoteRequest {
  content: string;
  title?: string | null;
  tags?: string[] | null;
}

/** Fetch the current user's notes from `GET /notes/`. */
export function listNotes(): Promise<NoteDTO[]> {
  return request<NoteDTO[]>("/notes/", { method: "GET" });
}

/** Create a note for the current user through `POST /notes/`. */
export function createNote(payload: CreateNoteRequest): Promise<NoteDTO> {
  return request<NoteDTO>("/notes/", { method: "POST", body: payload });
}
