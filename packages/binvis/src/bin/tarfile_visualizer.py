from typing import List, Dict, Tuple

import os
import json
import argparse
import tarfile
import multiprocessing

from functools import partial

from binvis.binvis import (
    visualize_binary,
    build_mask_from_spans,
)

from binvis.utils import (
    extract_diff_files,
    extract_diff_bytearray_spans_from_tarfile,
)

try:
    from incode_cloud.google_storage import gcs_upload_to_blob
except ImportError:
    print(
        (
            "Attempted import of cloud functions for `google-cloud-storage` failed. "
            "Uploading capability to google cloud is disabled."
        )
    )


OUT_FOLDER = os.path.abspath("../images")


def parse_args():
    """
    Command line arguments for the `container-builder` script.
    """

    parser = argparse.ArgumentParser(
        description="Build a container image for a given tool batch."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--tar_folder",
        action="store",
        dest="tar_folder",
        help="Define the `.tar` folder to parse.",
    )

    group.add_argument(
        "--tar_meta_path",
        action="store",
        dest="tar_meta_path",
        help="Path where the `.tar` metadata `.json` file will be stored.",
    )

    parser.add_argument(
        "--out_folder",
        action="store",
        dest="out_folder",
        help="Define the output folder for the produced images.",
        default=OUT_FOLDER,
    )

    parser.add_argument(
        "-c",
        "--color_map",
        action="store",
        nargs="+",
        dest="color_map",
        default=["class", "magnitude", "structure"],
        choices=["class", "hilbert", "entropy", "magnitude", "structure"],
        help=(
            "Choose the color map to be applied on the input byte array. "
            "If multiple colormaps are given, an image will be created "
            "with information from each colormap encoded in a different channel."
        ),
    )

    parser.add_argument(
        "-m",
        "--layout_map",
        action="store",
        dest="layout_map",
        default="hilbert",
        choices=["hilbert", "zigzag"],
        help="Pixel layout map. Can be any supported curve from the `scurve_np` module.",
    )

    parser.add_argument(
        "--size",
        action="store",
        dest="size",
        default=1024,
        type=int,
        help="Image width in pixels.",
    )

    parser.add_argument(
        "--layout_type",
        dest="layout_type",
        default="unrolled",
        choices=["unrolled_n", "unrolled", "square"],
        help="Image aspect ratio - square (1x1), unrolled (1x4), unrolled_n (1xn)",
    )

    parser.add_argument(
        "--upload-to-cloud",
        action="store",
        dest="upload_to_cloud",
        type=int,
        help="1 to upload file to cloud storage, 0 otherwise.",
        default=0,
    )

    parser.add_argument(
        "--cores",
        action="store",
        dest="cores",
        type=int,
        help="Define the cores to be used in parallel.",
    )

    return parser.parse_args()


def get_tar_paths_from_folder(tar_folder: str) -> List[str]:
    """
    Get all `.tar` files from a directory.
    """
    return [
        os.path.join(tar_folder, f)
        for f in os.listdir(tar_folder)
        if f.endswith(".tar")
    ]


def parse_tar_meta_json(tar_meta_file: str) -> List[Dict]:
    """
    Parse a `.json` file with tar metadata, exported from the
    `docker_builder` script.
    """
    FAILED = ("failed", "large-image-size")

    with open(tar_meta_file, "r") as f:
        tar_meta = json.load(f)

    tar_paths = [record["path"] for record in tar_meta if record["label"] not in FAILED]
    tar_masks_meta = []

    # Build mask metadata from file diffs information:
    # 1. Get paths from diffs metadata.
    # 2. Get diffs on actual bytearray.
    # 3. Organize data
    for record in tar_meta:

        if record["label"] in FAILED:
            continue

        tar_path = record["path"]

        diffs = record.get("diffs")

        if diffs is None:
            continue

        diff_files = extract_diff_files(diffs)

        spans = extract_diff_bytearray_spans_from_tarfile(tar_path, diff_files)

        tar_masks_meta.append({"spans": spans, "tar_path": tar_path})

    return tar_paths, tar_masks_meta


def upload_images_to_cloud(img_folder, filename, bucket_name, *prefix_args) -> None:
    """
    Upload files to cloud. Use `tar_metadata`.
    """
    source_path = os.path.join(img_folder, filename)

    prefix = "-".join([str(arg) for arg in prefix_args])

    dest_blob = os.path.join("images", prefix, filename)

    try:
        gcs_upload_to_blob(bucket_name, source_path, dest_blob)
        os.remove(source_path)

    except Exception:
        pass


def parse_path(path, add_suffix: str | None = None):
    """
    Extract filename from path and add suffix.
    """
    # Get path tail part, split `.tar` suffix, add `.png`
    _, filename = os.path.split(path)
    filename, _ = os.path.splitext(filename)

    return filename + "." + add_suffix.lstrip(".") if add_suffix else filename


def tar_file_to_image_converter(tar_path: str, out_folder: str, **kwargs) -> None:
    """
    Convert a tar file to a container image.
    """
    filename = parse_path(tar_path, ".png")

    kw = {"color_block": False, "show_progress": False}
    kw.update(kwargs)

    with open(tar_path, "rb") as f:
        byte_array = f.read()

    img = visualize_binary(byte_array=byte_array, **kw)

    img.save(os.path.join(out_folder, filename), format="png")

    return filename


def mask_meta_to_mask_converter(tar_mask_meta: Dict, out_folder: str, **kwargs) -> None:
    """
    Build an image mask for a given `.tar` with difference spans.
    """
    spans = tar_mask_meta["spans"]
    tar_path = tar_mask_meta["tar_path"]
    n_bytes = os.path.getsize(tar_path)

    filename = parse_path(tar_path, ".mask.png")

    kw = {"show_progress": False}
    kw.update(kwargs)

    img = build_mask_from_spans(n_bytes=n_bytes, spans=spans, **kw)

    img.save(os.path.join(out_folder, filename), format="png")

    return filename


def main() -> None:
    """
    Main function for the `container-builder` script.
    """
    args = parse_args()

    # Gather `tar` data.
    if args.tar_folder:
        tar_paths = get_tar_paths_from_folder(args.tar_folder)

    elif args.tar_meta_path:
        tar_paths, tar_masks_meta = parse_tar_meta_json(args.tar_meta_path)

    else:
        raise ValueError(
            "Neither `args.tar_folder` or `args.tar_meta_path` "
            "are provided. One of the two should be available."
        )

    print(f"Total `.tar` files to be converted to images: {len(tar_paths)}")

    # Create output folder if not exists
    out_folder = args.out_folder
    os.makedirs(out_folder, exist_ok=True)

    # Handle kwargs for image and mask creation.
    image_kw = {
        "size": args.size,
        "color_map": args.color_map,
        "layout_map": args.layout_map,
        "layout_type": args.layout_type,
    }

    mask_kw = {
        "size": args.size,
        "layout_map": args.layout_map,
        "layout_type": args.layout_type,
    }

    # Creating images from `tar` files
    print("Creating images from `.tar` files.")

    if args.cores == 1:
        for tar_path in tar_paths:

            filename = tar_file_to_image_converter(tar_path, out_folder, **image_kw)

            if args.upload_to_cloud:

                bucket_name = "incode-sa-tarball-images"
                upload_images_to_cloud(
                    out_folder,
                    filename,
                    bucket_name,
                    image_kw["size"],
                    image_kw["layout_type"],
                )

    else:
        func = partial(tar_file_to_image_converter, out_folder=out_folder, **image_kw)

        with multiprocessing.Pool(args.cores) as pool:

            for filename in pool.imap(func, tar_paths):

                if args.upload_to_cloud:

                    bucket_name = "incode-sa-tarball-images"
                    upload_images_to_cloud(
                        out_folder,
                        filename,
                        bucket_name,
                        image_kw["size"],
                        image_kw["layout_type"],
                    )

    # Build masks for malware `.tar` files.
    if args.tar_meta_path:

        print("Building masks for malwares from difference metadata.")

        if args.cores == 1:

            for tar_mask_meta in tar_masks_meta:

                filename = mask_meta_to_mask_converter(
                    tar_mask_meta, out_folder=out_folder, **mask_kw
                )

                if args.upload_to_cloud:

                    bucket_name = "incode-sa-tarball-images"
                    upload_images_to_cloud(
                        out_folder,
                        filename,
                        bucket_name,
                        image_kw["size"],
                        image_kw["layout_type"],
                    )

        else:
            func = partial(
                mask_meta_to_mask_converter, out_folder=out_folder, **mask_kw
            )

            with multiprocessing.Pool(args.cores) as pool:

                for filename in pool.imap(func, tar_masks_meta):

                    if args.upload_to_cloud:

                        bucket_name = "incode-sa-tarball-images"
                        upload_images_to_cloud(
                            out_folder,
                            filename,
                            bucket_name,
                            mask_kw["size"],
                            mask_kw["layout_type"],
                        )


if __name__ == "__main__":
    main()
