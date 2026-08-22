import io
import tempfile
import zipfile
from pathlib import Path


class RepositoryCheckout:
    """
    Extracts a GitHub repository ZIP archive into a
    temporary directory so DevGuardian can inspect it.
    """

    def checkout(
        self,
        archive_bytes: bytes,
    ) -> str:
        """
        Extract the repository archive.

        Returns:
            Path to the extracted repository root.
        """

        # -------------------------------------------------
        # Create temporary directory
        # -------------------------------------------------

        temp_directory = tempfile.mkdtemp(
            prefix="devguardian_repo_"
        )

        temp_path = Path(temp_directory)

        # -------------------------------------------------
        # Extract ZIP archive
        # -------------------------------------------------

        with zipfile.ZipFile(
            io.BytesIO(archive_bytes)
        ) as archive:

            archive.extractall(temp_path)

        # -------------------------------------------------
        # GitHub zipball usually contains one top-level
        # directory such as:
        #
        # arundhoti-aru17-devguardian-demo-target-abc123/
        # -------------------------------------------------

        directories = [
            path
            for path in temp_path.iterdir()
            if path.is_dir()
        ]

        if len(directories) == 1:
            repository_root = directories[0]
        else:
            repository_root = temp_path

        print(
            f"📁 Repository extracted to: "
            f"{repository_root}"
        )

        return str(repository_root)