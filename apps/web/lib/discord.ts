import { apiRequest } from "@/lib/api";

export type DiscordGuildConfig = {
  id: string;
  guild_id: string;
  enabled: boolean;
  allowed_channel_ids: string[];
  moderator_channel_id: string | null;
  default_visibility: "public" | "private";
  per_user_limit_per_minute: number;
  per_channel_limit_per_minute: number;
  per_guild_limit_per_minute: number;
  daily_capacity: number;
  thread_behavior: "none" | "thread";
  retention_days: number;
  enabled_commands: string[];
  created_at: string;
  updated_at: string;
};

export type DiscordEscalation = {
  id: string;
  message_id: string | null;
  guild_id: string | null;
  channel_id: string | null;
  question: string;
  answer_state: string;
  citations: Array<Record<string, unknown>>;
  request_id: string;
  status: "open" | "assigned" | "resolved" | "duplicate" | "out_of_scope";
  assigned_to: string | null;
  human_response: string | null;
  delivery_status: "pending" | "delivered" | "failed";
  created_at: string;
  updated_at: string;
};

export async function fetchDiscordGuildConfig(
  guildId: string,
): Promise<DiscordGuildConfig> {
  return apiRequest(
    `/api/v1/discord/guilds/${guildId}`,
    undefined,
    "Discord guild config failed",
  );
}

export async function updateDiscordGuildConfig(
  guildId: string,
  payload: Partial<
    Pick<
      DiscordGuildConfig,
      | "enabled"
      | "allowed_channel_ids"
      | "moderator_channel_id"
      | "default_visibility"
      | "per_user_limit_per_minute"
      | "per_channel_limit_per_minute"
      | "per_guild_limit_per_minute"
      | "daily_capacity"
      | "thread_behavior"
      | "retention_days"
      | "enabled_commands"
    >
  >,
): Promise<DiscordGuildConfig> {
  return apiRequest(
    `/api/v1/discord/guilds/${guildId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Discord guild update failed",
  );
}

export async function fetchDiscordEscalations(
  status?: string,
): Promise<DiscordEscalation[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  return apiRequest(
    `/api/v1/discord/escalations?${params.toString()}`,
    undefined,
    "Discord escalations failed",
  );
}

export async function updateDiscordEscalation(
  escalationId: string,
  payload: Partial<
    Pick<
      DiscordEscalation,
      "status" | "assigned_to" | "human_response" | "delivery_status"
    >
  >,
): Promise<DiscordEscalation> {
  return apiRequest(
    `/api/v1/discord/escalations/${escalationId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Discord escalation update failed",
  );
}
