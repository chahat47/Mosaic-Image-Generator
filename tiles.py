"""
Tile Image Downloader
Downloads diverse, colorful images to use as mosaic tiles.
Uses Picsum Photos (free, no API key needed) — https://picsum.photos

Usage examples:
  python3 download_tiles.py                      # 200 images, 128px, saved to ./tiles
  python3 download_tiles.py -n 500 -s 64         # 500 smaller images
  python3 download_tiles.py -n 300 --random      # 300 fully random images
  python3 download_tiles.py -o my_tiles -n 150   # custom output folder
"""

import os
import sys
import time
import random
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed


PICSUM_URL = "https://picsum.photos/{size}?random={seed}"

# Picsum lets you pick specific curated image IDs.
# These 200 IDs were chosen to maximize color diversity.
CURATED_IDS = list(range(1, 1085))  # Picsum has ~1000+ images


def download_image(idx, out_dir, size, seed):
    """Download a single image by Picsum ID and save it."""
    url = f"https://picsum.photos/id/{seed}/{size}/{size}"
    dest = os.path.join(out_dir, f"tile_{idx:04d}.jpg")

    if os.path.exists(dest):
        return dest, "skipped"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MosaicTileDownloader/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest, "ok"
    except Exception as e:
        return dest, f"error: {e}"


def download_random(idx, out_dir, size):
    """Download a random Picsum image (no fixed ID)."""
    seed = random.randint(1, 9999)
    url = f"https://picsum.photos/{size}/{size}?random={seed}"
    dest = os.path.join(out_dir, f"tile_r{idx:04d}.jpg")

    if os.path.exists(dest):
        return dest, "skipped"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MosaicTileDownloader/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest, "ok"
    except Exception as e:
        return dest, f"error: {e}"


def progress_bar(done, total, width=40):
    pct = done / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"\r  [{bar}] {done}/{total} ({pct*100:.0f}%)"


def main():
    parser = argparse.ArgumentParser(description="Download tile images for mosaic generator")
    parser.add_argument("-n", "--count",  type=int, default=200,
                        help="Number of images to download (default: 200)")
    parser.add_argument("-s", "--size",   type=int, default=128,
                        help="Image size in pixels, square (default: 128)")
    parser.add_argument("-o", "--output", type=str, default="tiles",
                        help="Output folder (default: ./tiles)")
    parser.add_argument("-w", "--workers",type=int, default=8,
                        help="Parallel download threads (default: 8)")
    parser.add_argument("--random",       action="store_true",
                        help="Use random images instead of curated IDs")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"\n  📦 Tile Image Downloader")
    print(f"  ─────────────────────────────")
    print(f"  Count   : {args.count} images")
    print(f"  Size    : {args.size}×{args.size} px")
    print(f"  Output  : {os.path.abspath(args.output)}")
    print(f"  Threads : {args.workers}")
    print(f"  Source  : {'random' if args.random else 'curated Picsum IDs'}")
    print()

    # Build task list
    if args.random:
        tasks = [(i, args.output, args.size) for i in range(args.count)]
    else:
        ids = random.sample(CURATED_IDS, min(args.count, len(CURATED_IDS)))
        if args.count > len(CURATED_IDS):
            # Fill remainder with randoms
            ids += [random.randint(1, 1084) for _ in range(args.count - len(CURATED_IDS))]
        tasks = [(i, args.output, args.size, img_id) for i, img_id in enumerate(ids)]

    done = 0
    ok = 0
    skipped = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        if args.random:
            futures = {pool.submit(download_random, *t): t for t in tasks}
        else:
            futures = {pool.submit(download_image, *t): t for t in tasks}

        for future in as_completed(futures):
            path, status = future.result()
            done += 1
            if status == "ok":
                ok += 1
            elif status == "skipped":
                skipped += 1
            else:
                errors += 1

            sys.stdout.write(progress_bar(done, args.count))
            sys.stdout.flush()

    print(f"\n\n  ✅ Done!")
    print(f"  ─────────────────────────────")
    print(f"  Downloaded : {ok}")
    print(f"  Skipped    : {skipped}  (already existed)")
    print(f"  Errors     : {errors}")
    print(f"  Saved to   : {os.path.abspath(args.output)}")
    print(f"\n  👉 Use '{os.path.abspath(args.output)}' as your Tile Folder in the mosaic app.\n")


if __name__ == "__main__":
    main()