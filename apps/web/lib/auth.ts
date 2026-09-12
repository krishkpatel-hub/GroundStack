import { apiRequest } from "@/lib/api";

export type AuthInfo = {
  authenticated: boolean;
  anonymous?: boolean;
  subject?: string;
  roles: string[];
  admin: boolean;
};

export async function fetchAuthInfo(signal?: AbortSignal): Promise<AuthInfo> {
  try {
    return await apiRequest("/api/v1/auth/me", { signal }, "Auth check failed");
  } catch {
    return { authenticated: false, anonymous: true, roles: [], admin: false };
  }
}
