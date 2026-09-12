export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const API_UNAVAILABLE_MESSAGE =
  "GroundStack cannot reach the API. Start the local backend, then try again.";

export function friendlyApiError(error: unknown, fallback: string): Error {
  if (error instanceof TypeError) {
    return new Error(API_UNAVAILABLE_MESSAGE);
  }
  if (error instanceof Error) return error;
  return new Error(fallback);
}

export async function apiErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body = (await response.json()) as {
      error?: { message?: string };
      detail?: unknown;
    };
    if (body.error?.message) return body.error.message;
    if (typeof body.detail === "string") return body.detail;
  } catch {
    return fallback;
  }
  return fallback;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  fallback = "Request failed",
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      ...init,
    });
  } catch (error) {
    throw friendlyApiError(error, fallback);
  }
  if (!response.ok) {
    throw new Error(
      await apiErrorMessage(response, `${fallback} with ${response.status}`),
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
