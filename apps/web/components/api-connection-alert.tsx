"use client";

import { AlertTriangle } from "lucide-react";

export const API_UNAVAILABLE_MESSAGE =
  "GroundStack cannot reach the API. Start the local backend, then try again.";

export function isApiUnavailableMessage(message: string | null | undefined) {
  return Boolean(message?.startsWith(API_UNAVAILABLE_MESSAGE));
}

export function ApiConnectionAlert({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  const apiUnavailable = isApiUnavailableMessage(message);

  return (
    <div className="inline-alert" role="alert">
      <AlertTriangle className="inline h-4 w-4" aria-hidden /> {message}
      {apiUnavailable && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className="button min-h-9" type="button" onClick={onRetry}>
            Retry connection
          </button>
          <details className="dev-details">
            <summary>Development details</summary>
            <p>
              Expected local API: <code>http://localhost:8000</code>. Start
              FastAPI and PostgreSQL with the documented local commands.
            </p>
          </details>
        </div>
      )}
    </div>
  );
}
