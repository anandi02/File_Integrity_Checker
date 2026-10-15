
import hashlib
import json
from pathlib import Path
from datetime import datetime

# Project folders and output files
PROJECT_DIR = Path(__file__).resolve().parent
TARGET_DIR = PROJECT_DIR / "sample_files"
BASELINE_FILE = PROJECT_DIR / "baseline.json"
REPORT_FILE = PROJECT_DIR / "integrity_report.txt"


def calculate_hash(file_path):
    """Calculate a file's SHA-256 hash."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_file_hashes():
    """Calculate hashes for all files in the test folder."""
    file_hashes = {}

    if not TARGET_DIR.exists():
        print("Error: sample_files folder was not found.")
        return None

    for file_path in sorted(TARGET_DIR.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(TARGET_DIR).as_posix()

            try:
                file_hashes[relative_path] = calculate_hash(file_path)
            except OSError as error:
                print(f"Could not read {relative_path}: {error}")

    return file_hashes


def save_baseline():
    """Save the current hashes as the trusted baseline."""
    hashes = get_file_hashes()

    if hashes is None:
        return

    if not hashes:
        print("No readable files found in sample_files.")
        return

    data = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": hashes
    }

    BASELINE_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )

    print(f"\nBaseline saved: {BASELINE_FILE}")
    print(f"Files recorded: {len(hashes)}")
    print("Keep this baseline safe and do not overwrite it")
    print("until you intentionally want a new reference.")


def check_integrity():
    """Compare current file hashes with the baseline."""
    if not BASELINE_FILE.exists():
        print("No baseline found. Choose option 1 first.")
        return

    try:
        baseline_data = json.loads(
            BASELINE_FILE.read_text(encoding="utf-8")
        )
        baseline = baseline_data["files"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        print("Baseline is unreadable or has an invalid format.")
        return

    current = get_file_hashes()

    if current is None:
        return

    report = []
    report.append("===== FILE INTEGRITY REPORT =====")
    report.append(
        "Checked at: " + datetime.now().isoformat(timespec="seconds")
    )
    report.append(f"Baseline files: {len(baseline)}")
    report.append(f"Current files: {len(current)}")
    report.append("")

    changed = []
    added = []
    missing = []

    for name, old_hash in baseline.items():
        if name not in current:
            missing.append(name)
        elif current[name] != old_hash:
            changed.append(name)

    for name in current:
        if name not in baseline:
            added.append(name)

    if not changed and not added and not missing:
        report.append("RESULT: No changes detected.")
    else:
        report.append("RESULT: File differences detected.")

    for name in changed:
        report.append(f"MODIFIED: {name}")

    for name in added:
        report.append(f"NEW FILE: {name}")

    for name in missing:
        report.append(f"MISSING: {name}")

    report.append("")
    report.append(f"Modified files: {len(changed)}")
    report.append(f"New files: {len(added)}")
    report.append(f"Missing files: {len(missing)}")
    report.append(
        "\nNote: A difference indicates a file change, "
        "not necessarily malicious activity."
    )

    output = "\n".join(report)
    print("\n" + output)

    REPORT_FILE.write_text(output, encoding="utf-8")
    print(f"\nReport saved: {REPORT_FILE}")


def main():
    while True:
        print("\n===== FILE INTEGRITY CHECKER =====")
        print("1. Create or update baseline")
        print("2. Check file integrity")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            save_baseline()
        elif choice == "2":
            check_integrity()
        elif choice == "3":
            print("Exiting File Integrity Checker.")
            break
        else:
            print("Invalid choice. Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
