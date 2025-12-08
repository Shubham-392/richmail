from pathlib import Path


class TranscationLogHierarchy:
    """
    Sets a system for logging the files in specific pattern

    files created under the `transcations` directory have pattern

    transcation_*.log
    """

    current_direct = Path.cwd()
    directory_path = current_direct / "transcations"
    transcation_file_pattern = "transcation_*.log"

    def __init__(self):
        pass

    def make_dir(self):
        self.directory_path.mkdir(exist_ok=True)

    def next_suffix(self):
        if self.directory_path.exists():
            current_suffix = len(
                [
                    file
                    for file in self.directory_path.glob("transcation_*.log")
                    if file.is_file()
                ]
            )
        next_suffix = f"{current_suffix + 1:04d}"
        return next_suffix

    def transcation_path(self, next_suffix: str):
        "return next file path for transcation log to create"
        file_path = self.directory_path / f"transcation_{next_suffix}.log"
        return file_path

    def create_log(self):
        self.make_dir()
        suffix = self.next_suffix()
        log_path = self.transcation_path(suffix)
        return log_path


transc = TranscationLogHierarchy()


# class SessionsLogHierarchy:
#     """
#     Sets a system for logging the files in specific pattern

#     files created under the `transcations` directory have pattern

#     transcation_*.log
#     """

#     current_direct = Path.cwd()
#     directory_path = current_direct / "sessions"

#     transcation_file_pattern = "session_*.log" # here * means the {threadID}



#     def __init__(self):
#         pass

#     def make_dir(self):
#         self.directory_path.mkdir(exist_ok=True)
