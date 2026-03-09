from datetime import datetime
from termcolor import colored
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI


class CustomLogger:
    """
    Manages logging history internally via an instance attribute, avoiding global state.
    """

    def __init__(self):
        self.logs: list[str] = []

    def log(
        self,
        msg: str,
        color: str = "white",
        bold: bool = False,
        phase_name: str | None = None,
    ) -> None:
        """
        Logs a message with ISO 8601 timestamp, optional phase name, and color/bold formatting.
        Also stores raw log entry without ANSI codes.
        """
        now: str = datetime.now().isoformat()
        entry: str = now

        if phase_name != None:  # Add phase name if provided
            entry += colored(f" [{phase_name}]", color="yellow")
        entry += colored(" > ", color="dark_grey")

        if bold == False:  # Add message with color / bolding
            entry += colored(msg, color=color)
        else:
            entry += colored(msg, color=color, attrs=["bold"])

        # Store log without ANSI codes
        raw_entry: str = now
        if phase_name != None:
            raw_entry += f" [{phase_name}]"
        raw_entry += " > " + msg
        self.logs.append(raw_entry)

        print_formatted_text(ANSI(entry))

    def write_logs_to_file(self, filepath: str) -> None:
        """
        Helper function to write the current logs to a file
        """
        with open(filepath, "w") as f:
            for log_entry in self.logs:
                # Strip ANSI codes for file writing (this is already done when appending to self.logs)
                f.write(log_entry + "\n")

    def printf(self, msg: str, color: str = "white", bold: bool = False) -> None:
        """
        Helper function to get around prompt_toolkit printing issues w/ termcolor
        """
        if bold == False:
            print_formatted_text(ANSI(colored(msg, color=color)))
        else:
            print_formatted_text(ANSI(colored(msg, color=color, attrs=["bold"])))


# Default instance for compatibility, though Phase/Autosequence should use this instance's methods
logger = CustomLogger()
log = logger.log
printf = logger.printf
write_logs_to_file = logger.write_logs_to_file
