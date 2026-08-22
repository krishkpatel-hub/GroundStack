from __future__ import annotations

import json

from app.services.discord.registration import command_payloads, installation_url


def main() -> None:
    print(
        json.dumps(
            {
                "installation_url": installation_url(),
                "commands": command_payloads(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
