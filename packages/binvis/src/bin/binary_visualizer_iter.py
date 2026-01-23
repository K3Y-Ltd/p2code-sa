#!/usr/bin/env python
import os
import sys

from binvis.binvis_iter import visualize_binary_iter

import argparse


def parse_args():
    """
    Command line arguments for the `binvis` script.
    """
    parser = argparse.ArgumentParser(
        description="Convert arbitrary binary files to images."
    )

    parser.add_argument(
        "--in_path",
        action="store",
        dest="in_path",
        help="Define file path to input file to visualize.",
    )

    parser.add_argument(
        "--out_path",
        action="store",
        dest="out_path",
        help="Define file path to output `png` image.",
    )

    parser.add_argument(
        "-c",
        "--color_map",
        action="store",
        nargs="+",
        dest="color_map",
        default="class",
        choices=["class", "magnitude", "structure"],
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
        "-n",
        "--namesuffix",
        action="store",
        dest="suffix",
        default="",
        help="Suffix for generated file names. Ignored if destination is specified.",
    )

    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        default=True,
        dest="progress",
        help="Don't show progress bar - print the destination file name.",
    )

    parser.add_argument(
        "--size",
        action="store",
        dest="size",
        default=256,
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
        "--step",
        dest="step",
        default=None,
        help="Sampling step for image downsampling. Used in `unrolled` layout.",
    )

    parser.add_argument(
        "--color_block",
        action="store",
        dest="color_block",
        default=None,
        help="Mark a block of data with a specified color. Format: hexstartaddr:hexendaddr[:hexcolor]",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", dest="quiet", default=False
    )

    args = parser.parse_args()

    return args


def main() -> None:
    """
    Main function of the binvis script.
    """
    args = parse_args()

    in_path = getattr(args, "in_path", None)
    out_path = getattr(args, "out_path", None)

    if in_path is None:
        raise ValueError("Please specify input file.")

    if out_path is None:
        raise ValueError("Please specify output file.")

    size = int(args.size)
    color_map = args.color_map
    layout_map = args.layout_map
    layout_type = args.layout_type
    color_block = args.color_block
    progress = args.progress
    step = int(args.step) if args.step else None

    img = visualize_binary_iter(
        path=in_path,
        size=size,
        color_map=color_map,
        layout_map=layout_map,
        layout_type=layout_type,
        color_block=color_block,
        show_progress=progress,
        chunk_size=20*512,
        step=step,
    )

    img.save(out_path, format="png")


if __name__ == "__main__":
    main()
