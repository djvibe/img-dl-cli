#!/usr/bin/env python3
import argparse
import logging
import sys
import os
from downloader import ImageDownloader

def setup_logging(log_dir: str):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'cli.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description="Download high-resolution images from Google Images.")
    parser.add_argument("query", help="Search query for images")
    parser.add_argument("-n", "--num", type=int, default=5, help="Number of images to download (default: 5)")
    parser.add_argument("-s", "--size", type=int, default=180, help="Minimum file size in KB (default: 180)")
    parser.add_argument("-t", "--type", choices=["all", "photo", "clipart", "lineart", "gif"], default="photo", 
                        help="Image type filter (default: photo)")
    parser.add_argument("-o", "--output", default="images", help="Output directory (default: images)")
    parser.add_argument("-l", "--logs", default="logs", help="Log directory (default: logs)")

    args = parser.parse_args()

    setup_logging(args.logs)
    logger = logging.getLogger(__name__)

    downloader = ImageDownloader(download_path=args.output, log_dir=args.logs)
    
    print(f"[*] Searching for '{args.query}' and downloading {args.num} images...")
    result = downloader.download_images(
        query=args.query,
        num_images=args.num,
        min_size_kb=args.size,
        image_type=args.type
    )

    if result["status"] == "success":
        print(f"\n[+] Successfully downloaded {result['downloaded']} images.")
        for f in result["files"]:
            print(f"  - {f}")
    else:
        print(f"\n[-] Error occurred: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
