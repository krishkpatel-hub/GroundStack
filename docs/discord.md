# GroundStack Discord Integration

GroundStack's Discord integration is a slash-command adapter over the existing
GroundStack retrieval and generation stack. It does not scan ordinary channel
messages, does not read surrounding channel history, and does not require the
privileged Message Content intent.

## Architecture

```text
Discord interaction
-> FastAPI /integrations/discord/interactions
-> Ed25519 signature and timestamp verification
-> replay/deduplication record
-> deferred Discord response
-> encrypted Discord job
-> Discord worker
-> GroundStack hybrid retrieval, reranking, generation, citation validation
-> Discord renderer with allowed_mentions disabled
-> feedback or escalation controls
```

The initial interaction endpoint only verifies, authorizes, records, and queues.
Retrieval and generation run in the worker so the endpoint can defer inside
Discord's response window. Interaction tokens are encrypted, expire quickly, and are
cleared after delivery.

## Commands

Member commands:

- `/ask question:<text> visibility:<public|private>`
- `/help`
- `/status`
- `/privacy`
- `/delete-my-data`

Moderator commands:

- `/groundstack enable`
- `/groundstack disable`
- `/groundstack configure`
- `/groundstack channels`
- `/groundstack limits`
- `/groundstack stats`

GroundStack processes only the text explicitly submitted through `/ask`. DMs are
disabled by default with `DISCORD_ALLOW_DMS=false`.

## Minimal Permissions

The local helper `make discord-commands-json` prints command payloads and an
installation URL. The URL requests:

- `applications.commands`: required for slash commands.
- Bot `Send Messages`: required only for future moderator-channel escalation
  delivery and non-ephemeral channel responses.
- Bot `Embed Links`: required for citation-rich answer embeds.

It does not request Administrator, Manage Server, Manage Roles, Ban Members, Kick
Members, View Audit Log, Guild Members intent, Presence intent, or Message Content
intent.

## Privacy

Stored Discord records are intentionally narrow:

- interaction ID, application ID, guild ID, and channel ID
- keyed HMAC user identifier
- explicit `/ask` question
- answer delivery state
- feedback, escalation, and deletion status

GroundStack does not store usernames, display names, member lists, avatars,
presence, biographies, relationships, demographics, normal channel history, bot
tokens, interaction tokens in plaintext, raw request bodies, or authorization
headers.

Discord records are marked `source_platform=discord` and `training_eligible=false`.
Training-candidate queries exclude them, approval rejects them, and feedback does
not grant training permission.

## Deletion

Users can run `/delete-my-data`, then confirm the deletion button. The backend
deletes Discord feedback, escalations, interactions, queued jobs, and generated
messages associated with the user's keyed HMAC in that guild. Server owners can
disable a guild config from the admin UI.

## Sandbox Setup

1. Create a Discord application in the Discord Developer Portal.
2. Configure the bot identity.
3. Copy the application ID and public key into secret storage.
4. Generate the bot token and store it only in the deployment secret manager.
5. Set the interactions endpoint to `/integrations/discord/interactions`.
6. Add public privacy and terms URLs, such as `/discord/privacy` and `/discord/terms`.
7. Run `make discord-commands-json` and review the scopes and permissions.
8. Register guild-scoped commands in a private development server using the printed
   command payloads.
9. Keep `DISCORD_INTEGRATION_ENABLED=false` until the endpoint is reachable and
   signature verification has passed.
10. Rotate the token immediately if it is exposed.

Never commit real Discord values, paste tokens into chat, or include secrets in
screenshots.

## Environment Variables

- `DISCORD_INTEGRATION_ENABLED`
- `DISCORD_APPLICATION_ID`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_INTERACTION_TOKEN_ENCRYPTION_KEY`
- `DISCORD_IDENTITY_HMAC_KEY`
- `DISCORD_SIGNATURE_TOLERANCE_SECONDS`
- `DISCORD_DEFAULT_RETENTION_DAYS`
- `DISCORD_MAX_QUESTION_LENGTH`
- `DISCORD_QUEUE_TTL_SECONDS`
- `DISCORD_WORKER_BATCH_SIZE`
- `DISCORD_WORKER_MAX_RETRIES`
- `DISCORD_RESPONSE_BASE_URL`
- `DISCORD_FULL_ANSWER_BASE_URL`
- `DISCORD_ALLOW_DMS`

## Current Limits

The repository includes local implementation and mocked tests only. It does not
create a Discord application, install a bot, register commands against Discord,
provision paid services, or claim production Discord usage.
