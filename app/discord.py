import logging
import httpx

from .config import DISCORD_ENABLED, DISCORD_HOST, DISCORD_TARGET_USER

log = logging.getLogger("cooking-papa.discord")


async def send_preparation_request(recipe_title: str, ingredients: list[str], note: str | None) -> tuple[bool, str]:
    """Notify the Discord companion bot.

    Returns (success, info_message). If disabled, logs and returns success=False with a friendly note.
    TODO: plug the final POST format once confirmed by user.
    """
    lines = [f"🍳 Préparation demandée: **{recipe_title}**"]
    if ingredients:
        lines.append("Ingrédients:")
        lines.extend(f"- {i}" for i in ingredients)
    if note:
        lines.append(f"\nNote: {note}")
    message = "\n".join(lines)

    if not DISCORD_ENABLED:
        log.info("Discord disabled; would send:\n%s", message)
        return False, "Discord désactivé (stub). Requête enregistrée."

    if not DISCORD_TARGET_USER or not DISCORD_HOST:
        return False, "Configuration Discord incomplète."

    payload = {"user": DISCORD_TARGET_USER, "message": message}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{DISCORD_HOST}/dm/send", json=payload)
            r.raise_for_status()
        return True, "Envoyé sur Discord."
    except Exception as e:  # noqa: BLE001
        log.exception("Discord send failed")
        return False, f"Échec envoi Discord: {e}"
