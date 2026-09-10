/**
 * QuantAlpha Typed API Error Definition
 * Provides deterministic error classification for fail-closed research operations.
 */

export class ApiError extends Error {
  readonly status: number | null;
  readonly code: string;
  readonly details?: unknown;

  constructor(
    message: string,
    options: {
      status?: number | null;
      code?: string;
      details?: unknown;
    } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status ?? null;
    this.code = options.code ?? "API_ERROR";
    this.details = options.details;
  }
}

/**
 * Safely extracts user-meaningful error message without exposing backend stack traces.
 */
export function extractSafeMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const p = payload as Record<string, any>;
  if (typeof p.detail === "string") return p.detail;
  if (typeof p.detail?.message === "string") return p.detail.message;
  if (typeof p.message === "string") return p.message;
  if (typeof p.error?.message === "string") return p.error.message;
  if (typeof p.error === "string") return p.error;
  return null;
}

/**
 * Extracts structured error codes (e.g. UNIVERSE_DATA_UNAVAILABLE, INVALID_JSON).
 */
export function extractSafeCode(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const p = payload as Record<string, any>;
  if (typeof p.detail?.code === "string") return p.detail.code;
  if (typeof p.code === "string") return p.code;
  if (typeof p.error?.code === "string") return p.error.code;
  return null;
}
