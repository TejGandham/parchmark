import { ApiError } from "@/services/http";

/** Human-readable message for a failed artifacts request. */
export function errorDetail(caught: unknown): string {
  return caught instanceof ApiError
    ? caught.detail
    : "Something went wrong. Try again.";
}
