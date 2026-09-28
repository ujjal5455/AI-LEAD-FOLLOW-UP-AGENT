// Browser-side helper for calling the backend through the /api proxy.

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

/** Turn FastAPI's error body ({"detail": ...}) into one readable sentence. */
function readErrorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const issue = detail[0] as ValidationIssue;
    const field = issue.loc?.at(-1);
    return field ? `${String(field).replaceAll("_", " ")}: ${issue.msg}` : String(issue.msg);
  }
  return status >= 500
    ? "The server ran into a problem. Please try again in a moment."
    : `Request failed (HTTP ${status}).`;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Couldn't reach the server. Check your connection and try again.", 0);
  }

  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // Not JSON (e.g. the backend is down and the proxy returned an HTML error page).
  }
  if (!response.ok) throw new ApiError(readErrorMessage(data, response.status), response.status);
  return data as T;
}
