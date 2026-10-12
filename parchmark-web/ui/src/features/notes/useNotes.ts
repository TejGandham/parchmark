import { ref } from "vue";

import type { NoteMock } from "./mockNotes";
import {
  createNote as createNoteRequest,
  deleteNote as deleteNoteRequest,
  listNotes,
  updateNote as updateNoteRequest,
  type CreateNoteRequest,
  type NoteDTO,
  type UpdateNoteRequest,
} from "../../services/notes";
import { ApiError } from "../../services/http";

/**
 * Module-singleton notes store, mirroring the `useAuth.ts` pattern: reactive
 * refs are declared at module scope and shared across every `useNotes()` call.
 * Unlike auth, notes are fetched on demand rather than persisted client-side,
 * so there is no `useStorage` backing — the refs reset on reload.
 */

/** The user's notes, mapped from the backend DTO shape into `NoteMock`. */
const notes = ref<NoteMock[]>([]);

/** `true` while a {@link fetchNotes} call is in flight. */
const loading = ref(false);

/** Last error detail from a failed {@link fetchNotes}, or `null` when clean. */
const error = ref<string | null>(null);

/** `true` while a note create call is in flight. */
const creating = ref(false);

/** `true` while a note update call is in flight. */
const updating = ref(false);

/** The note id currently being deleted, or `null` when no delete is pending. */
const deletingId = ref<string | null>(null);

/** Last user-action mutation error, separate from the note-list load error. */
const mutationError = ref<string | null>(null);

function errorDetail(caught: unknown): string {
  return caught instanceof ApiError ? caught.detail : String(caught);
}

function mapDtoToNote(dto: NoteDTO): NoteMock {
  return {
    id: dto.id,
    content: dto.content,
    tags: dto.tags,
    createdAt: Date.parse(dto.createdAt),
    updatedAt: Date.parse(dto.updatedAt),
  };
}

/**
 * Load the user's notes from `GET /notes/` and replace {@link notes} with the
 * mapped result. Each {@link NoteDTO} is adapted to {@link NoteMock}:
 * - `createdAt`/`updatedAt` ISO-8601 strings are converted to epoch ms via
 *   `Date.parse`.
 * - `tags` is copied from the backend's normalized note tag contract.
 * - The backend `title` field is intentionally unused: the frontend derives
 *   titles client-side via `extractTitle(content)`. Carrying it on the DTO
 *   preserves the option to consume it later without another client change;
 *   this is a recorded reconciliation decision, not a missing field.
 *
 * On rejection, sets {@link error} to the `ApiError.detail` (or stringified
 * value for non-API errors) and leaves {@link notes} unchanged. {@link loading}
 * is reset in all paths via `finally`.
 */
export async function fetchNotes(): Promise<void> {
  loading.value = true;
  error.value = null;

  try {
    const dtos: NoteDTO[] = await listNotes();
    notes.value = dtos.map(mapDtoToNote);
  } catch (caught) {
    error.value = errorDetail(caught);
  } finally {
    loading.value = false;
  }
}

/** Default debounce window (ms) for coalescing live-event refetches. */
const REFETCH_DEBOUNCE_MS = 200;

let refetchTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Schedule a debounced {@link fetchNotes}. Calls made within `delayMs` of each
 * other collapse into a single refetch — used by the live note-events stream so
 * a burst of backend changes triggers one canonical reload, not one per event.
 */
export function scheduleRefetch(delayMs: number = REFETCH_DEBOUNCE_MS): void {
  if (refetchTimer !== null) {
    clearTimeout(refetchTimer);
  }
  refetchTimer = setTimeout(() => {
    refetchTimer = null;
    void fetchNotes();
  }, delayMs);
}

/** Cancel any pending {@link scheduleRefetch} (teardown helper). */
export function cancelScheduledRefetch(): void {
  if (refetchTimer !== null) {
    clearTimeout(refetchTimer);
    refetchTimer = null;
  }
}

export async function createNote(
  payload: CreateNoteRequest = { content: "# Untitled\n\n", tags: [] },
): Promise<NoteMock> {
  creating.value = true;
  mutationError.value = null;

  try {
    const created = mapDtoToNote(await createNoteRequest(payload));
    notes.value = [created, ...notes.value];
    return created;
  } catch (caught) {
    mutationError.value = errorDetail(caught);
    throw caught;
  } finally {
    creating.value = false;
  }
}

export async function updateNote(
  noteId: string,
  payload: UpdateNoteRequest,
): Promise<NoteMock> {
  updating.value = true;
  mutationError.value = null;

  try {
    const updated = mapDtoToNote(await updateNoteRequest(noteId, payload));
    notes.value = notes.value.map((note) =>
      note.id === noteId ? updated : note,
    );
    return updated;
  } catch (caught) {
    mutationError.value = errorDetail(caught);
    throw caught;
  } finally {
    updating.value = false;
  }
}

export async function deleteNote(noteId: string): Promise<void> {
  deletingId.value = noteId;
  mutationError.value = null;

  try {
    const response = await deleteNoteRequest(noteId);
    if (response.deleted_id !== noteId) {
      throw new ApiError(500, "Delete response did not match requested note");
    }
    notes.value = notes.value.filter((note) => note.id !== noteId);
  } catch (caught) {
    mutationError.value = errorDetail(caught);
    throw caught;
  } finally {
    deletingId.value = null;
  }
}

export function clearMutationError(): void {
  mutationError.value = null;
}

/**
 * Reactive notes store as a composable singleton. All consumers share one set
 * of module-level refs; calling this multiple times returns the same refs.
 */
export function useNotes() {
  return {
    notes,
    loading,
    error,
    creating,
    updating,
    deletingId,
    mutationError,
    fetchNotes,
    scheduleRefetch,
    cancelScheduledRefetch,
    createNote,
    updateNote,
    deleteNote,
    clearMutationError,
  };
}
