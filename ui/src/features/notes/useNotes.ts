import { ref } from "vue";

import type { NoteMock } from "./mockNotes";
import { listNotes, type NoteDTO } from "../../services/notes";
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

/**
 * Load the user's notes from `GET /notes/` and replace {@link notes} with the
 * mapped result. Each {@link NoteDTO} is adapted to {@link NoteMock}:
 * - `createdAt`/`updatedAt` ISO-8601 strings are converted to epoch ms via
 *   `Date.parse`.
 * - `tags` is forced to `[]` because the backend exposes no tags field yet
 *   (a known backend gap, not a silent drop).
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
    notes.value = dtos.map(
      (dto): NoteMock => ({
        id: dto.id,
        content: dto.content,
        tags: [],
        createdAt: Date.parse(dto.createdAt),
        updatedAt: Date.parse(dto.updatedAt),
      }),
    );
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.detail : String(caught);
  } finally {
    loading.value = false;
  }
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
    fetchNotes,
  };
}
