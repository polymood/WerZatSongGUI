import re
import sys
from pathlib import Path

from consts import ENV_FILE
from ..utils.messages import exit as exit_with_error, warning
from webhook import post_webhook
from ..audiotag import post_audiotag

# Regular expressions for key formats
ACOUSTID_KEY_REGEX   = re.compile(r'^[A-Za-z0-9_.-]{10}$')
AUDIOTAG_KEY_REGEX   = re.compile(r'^[a-z0-9]{32}$')
WEBHOOK_REGEX        = re.compile(r'^https://discord\.com/api/webhooks/\d+/[A-Za-z0-9_.-]+$')
DURATION_REGEX       = re.compile(r'^\d+:\d+$')

# Default values and limits
DEFAULT_DURATION         = '140:360'   # "min_seconds:max_seconds"
DEFAULT_EXTENSION        = 10          # seconds
MAX_DURATION_ALLOWED     = 600         # seconds
MIN_DURATION_ALLOWED     = 30          # seconds
MAX_EXTENSION_ALLOWED    = 25          # seconds
MIN_EXTENSION_ALLOWED    = 1           # seconds
WEBHOOK_MESSAGE          = (
    "Welcome to __WerZatSong__!\n"
    "Developed by **Nel** with contributions from **Numerophobe**, **AzureBlast** and **Mystic65**"
)


def request_value(prompt_text: str) -> str:
    """
    Prompt the user on stdin and return the stripped response.
    """
    try:
        return input(prompt_text).strip()
    except (EOFError, KeyboardInterrupt):
        # If the user aborts, exit gracefully
        sys.exit(1)


def _read_env_file() -> str:
    """
    Read the contents of the .env file and return as a string.
    If the file does not exist, return an empty string.
    """
    path = Path(ENV_FILE)
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8')


def _write_env_file(updated_content: str) -> None:
    """
    Overwrite the .env file with updated_content (UTF-8).
    """
    Path(ENV_FILE).write_text(updated_content, encoding='utf-8')


def validate_audiotag(key: str) -> str:
    """
    Ensure we have a valid Audiotag API key (32 lowercase hex chars).
    If 'key' is empty or invalid, prompt the user to paste one.
    Once we obtain a potentially valid key, call post_audiotag('info', True, key) to check it.
    If that call succeeds (success == True), write/update AUDIOTAG_KEY in .env and return it.
    If still invalid or the API check fails, exit with an error message.
    If the input 'key' was already valid, return None to indicate "no change needed".
    """
    if not key or not AUDIOTAG_KEY_REGEX.fullmatch(key):
        warning("Audiotag API key is not set in .env file. Please provide a valid Audiotag API key")
        user_input = request_value("Paste your Audiotag API key here: ")
        if AUDIOTAG_KEY_REGEX.fullmatch(user_input):
            # Attempt a trial "info" call to Audiotag to confirm the key actually works
            resp = post_audiotag('info', True, user_input)
            success = resp.get('success', False) if isinstance(resp, dict) else False
            if success:
                env_content = _read_env_file()
                if "AUDIOTAG_KEY=" in env_content:
                    updated = re.sub(r'AUDIOTAG_KEY=.*',
                                     f'AUDIOTAG_KEY={user_input}',
                                     env_content)
                else:
                    updated = env_content.rstrip("\n") + f"\nAUDIOTAG_KEY={user_input}\n"
                _write_env_file(updated)
                return user_input

        # If we reach here, the user_input was either syntactically wrong or the API check failed
        exit_with_error("The Audiotag API key you entered is invalid")

    # If original key was already valid, return None (no changes made)
    return None


def validate_duration(duration: str) -> str:
    """
    Given a string "min:max", confirm it's numeric and within [MIN_DURATION_ALLOWED, MAX_DURATION_ALLOWED].
    If valid, return the trimmed string. Otherwise return DEFAULT_DURATION.
    """
    if isinstance(duration, str) and duration.strip() and DURATION_REGEX.fullmatch(duration.strip()):
        min_sec, max_sec = map(int, duration.split(':'))
        if MIN_DURATION_ALLOWED <= min_sec < max_sec <= MAX_DURATION_ALLOWED:
            return duration.strip()
    return DEFAULT_DURATION


def validate_extension(extension) -> int:
    """
    Given a number (or something), check if it's an integer between MIN_EXTENSION_ALLOWED and MAX_EXTENSION_ALLOWED.
    If so, return it. Otherwise return DEFAULT_EXTENSION.
    """
    try:
        ext_int = int(extension)
        if MIN_EXTENSION_ALLOWED <= ext_int <= MAX_EXTENSION_ALLOWED:
            return ext_int
    except (ValueError, TypeError):
        pass
    return DEFAULT_EXTENSION


def validate_musicbrainz(key: str) -> str:
    """
    Ensure we have at least one valid AcoustID key. The .env variable can be a comma-separated list.
    Each key must match ACOUSTID_KEY_REGEX (10 alphanumeric/underscore/dot/dash chars).
    If the provided 'key' is empty or none of the comma-separated tokens are valid, prompt the user.
    Once the user pastes a comma-separated list of keys, filter them, rejoin, write to .env, and return.
    If still invalid, exit with an error. If the original key parameter was already OK, return None.
    """
    valid_tokens = None
    if key and isinstance(key, str):
        cand = [tok.strip() for tok in key.split(',')]
        valid_tokens = [tok for tok in cand if ACOUSTID_KEY_REGEX.fullmatch(tok)]
        if not valid_tokens:
            valid_tokens = None

    if not key or valid_tokens is None:
        warning("AcoustID API key is not set in .env file. Please provide a valid AcoustID API key")
        user_input = request_value("Paste your AcoustID API key here (comma-separated if multiple): ")
        tokens = [tok.strip() for tok in user_input.split(',')]
        valid_tokens = [tok for tok in tokens if ACOUSTID_KEY_REGEX.fullmatch(tok)]
        if valid_tokens:
            joined = ",".join(valid_tokens)
            env_content = _read_env_file()
            if "ACOUSTID_KEY=" in env_content:
                updated = re.sub(r'ACOUSTID_KEY=.*',
                                 f'ACOUSTID_KEY={joined}',
                                 env_content)
            else:
                updated = env_content.rstrip("\n") + f"\nACOUSTID_KEY={joined}\n"
            _write_env_file(updated)
            return joined
        else:
            exit_with_error("The AcoustID API key you entered is invalid")

    return None


def validate_webhook(webhook_url: str) -> str:
    """
    Ensure the Discord webhook URL is set and matches Discord's endpoint pattern.
    If missing/invalid, prompt the user for a webhook URL. Once provided and syntactically valid,
    immediately POST the welcome message to it via post_webhook(). If that call succeeds,
    write/update WEBHOOK_URL in .env and return it. If it fails or the URL is wrong, exit with error.
    If the original webhook_url parameter was already valid, return None.
    """
    if not webhook_url or not WEBHOOK_REGEX.fullmatch(webhook_url):
        warning("Discord webhook is not set in .env file. Please provide a valid Discord webhook URL")
        user_input = request_value("Paste your Discord webhook URL here: ")
        if WEBHOOK_REGEX.fullmatch(user_input):
            # Attempt to send the welcome message
            sent_ok = post_webhook(user_input, WEBHOOK_MESSAGE)
            if sent_ok:
                env_content = _read_env_file()
                if "WEBHOOK_URL=" in env_content:
                    updated = re.sub(r'WEBHOOK_URL=.*',
                                     f'WEBHOOK_URL={user_input}',
                                     env_content)
                else:
                    updated = env_content.rstrip("\n") + f"\nWEBHOOK_URL={user_input}\n"
                _write_env_file(updated)
                return user_input

        exit_with_error("The Discord webhook URL you entered is invalid")

    return None
