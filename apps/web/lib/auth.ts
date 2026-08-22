const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type AuthInfo = {
  authenticated: boolean;
  anonymous?: boolean;
  subject?: string;
  roles: string[];
  admin: boolean;
};

export async function fetchAuthInfo(signal?: AbortSignal): Promise<AuthInfo> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    return { authenticated: false, anonymous: true, roles: [], admin: false };
  }
  return response.json() as Promise<AuthInfo>;
}
