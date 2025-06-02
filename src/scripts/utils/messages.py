import sys
from colorama import init, Fore, Style

# Initialize colorama to enable ANSI color codes on all platforms
init(autoreset=True)

class Message:
    EMPTY   = Fore.LIGHTBLACK_EX
    ERROR   = Fore.LIGHTRED_EX
    INFO    = Fore.CYAN
    SUCCESS = Fore.LIGHTGREEN_EX
    WARNING = Fore.YELLOW

def empty(message: str):
    """
    Print a gray “[EMPTY]: <message>” to stdout.
    """
    print(f"{Message.EMPTY}[EMPTY]: {message}{Style.RESET_ALL}")

def exit(message: str):
    """
    Print a red “[ERROR]: <message>” to stderr, then terminate with exit code 1.
    """
    print(f"{Message.ERROR}[ERROR]: {message}{Style.RESET_ALL}", file=sys.stderr)
    sys.exit(1)

def info(message: str):
    """
    Print a cyan “[INFO]: <message>” to stdout.
    """
    print(f"{Message.INFO}[INFO]: {message}{Style.RESET_ALL}")

def success(message: str):
    """
    Print a bright green “[SUCCESS]: <message>” to stdout.
    """
    print(f"{Message.SUCCESS}[SUCCESS]: {message}{Style.RESET_ALL}")

def warning(message: str):
    """
    Print a yellow “[WARNING]: <message>” to stdout.
    """
    print(f"{Message.WARNING}[WARNING]: {message}{Style.RESET_ALL}")
