SYSTEM_REPAIR_COMMANDS = [
    (
        "SFC /Scannow",
        "Scans integrity of all protected system files and repairs files with problems when possible."
    ),
    (
        "Dism /Online /Cleanup-Image /CheckHealth",
        "Checks whether the image has been flagged as corrupted " +
        "by a failed process and whether the corruption can be repaired."
    ),
    (
        "Dism /Online /Cleanup-Image /ScanHealth",
        "Scans the image for component store corruption."
    ),
    (
        "Dism /Online /Cleanup-Image /RestoreHealth",
        "Scans the image for component store corruption, and then performs repair operations automatically."
    )
]

DISK_REPAIR_COMMANDS = [
    (
        "Chkdsk",
        "Checks a disk and displays a status report."
    ),
    (
        "Chkdsk /c",
        "NTFS only: Skips checking of cycles within the folder structure."
    ),
    (
        "Chkdsk /b",
        "NTFS only: Re-evaluates bad clusters on the volume (implies /R)"
    ),
    (
        "Chkdsk /f",
        "Fixes errors on the disk."
    ),
    (
        "Chkdsk /r",
        "Locates bad sectors and recovers readable information (implies /F, when /scan not specified)."
    ),
    (
        "Chkdsk /r /c",
        "NTFS only: Locates bad sectors and recovers readable information " +
        "and skips checking of cycles within the folder structure."
    )
]

IMAGE_CLEANUP_COMMANDS = [
    (
        "Dism /Online /Cleanup-Image /AnalyzeComponentStore",
        "Create a report of the WinSxS component store."
    ),
    (
        "Dism /Online /Cleanup-Image /StartComponentCleanup",
        "Clean up the superseded components and reduce the size of the component store."
    ),
    (
        "Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase",
        "Reset the base of superseded components, which can further reduce the component store size."
    ),
    (
        "Dism /Online /Cleanup-Image /revertpendingactions",
        "Revert any windows update pending actions."
    )
]
