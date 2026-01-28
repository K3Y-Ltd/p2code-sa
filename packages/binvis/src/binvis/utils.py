import tarfile

from typing import Dict, List, Tuple


def extract_diff_files(diffs: Dict) -> List[str]:
    """
    Get paths of modified files.
    """
    adds, dels, mods = [], [], []

    if diffs["Adds"]:
        adds = [item["Name"] for item in diffs["Adds"]]

    if diffs["Dels"]:
        dels = [item["Name"] for item in diffs["Dels"]]

    if diffs["Mods"]:
        mods = [item["Name"] for item in diffs["Mods"]]

    return adds + mods


def extract_diff_bytearray_spans_from_tarfile(
    tar_path: str, files: List[str]
) -> List[Tuple[int, int]]:
    """
    Get bytearray spans from a tarfile.

    Parameters
    ----------
    tar_path : str
        Path to tarfile we want to extract spans from.
    files : List[str]
        A list of files to search in the tarfile to get their spans.

    Returns
    -------
    spans : List[Dict]
        Return a list of span positions on the tarfile.
    """
    # Remove starting "/" character to match `tarfile` format
    files_set = set([file.lstrip("/") for file in files])

    spans = []

    with tarfile.open(tar_path, "r") as trf:

        for i, tar_info in enumerate(trf, 1):

            if tar_info.name not in files_set:
                continue

            start = tar_info.offset
            end = tar_info.offset_data + tar_info.size

            spans.append((start, end))

            if i % 1000 == 0:
                trf.members = []

    return spans
