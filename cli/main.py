"""AKPack CLI: compress, restore, inspect, verify."""
import argparse
import os
import sys
import tempfile
from core.compressor import compress_file
from core.restorer import restore_file
from core.container import read_header


def cmd_compress(args) -> None:
    r = compress_file(args.src, args.out)
    saved = 100 * (1 - r["compressed_size"] / r["orig_size"]) if r["orig_size"] else 0
    print(f"[OK] {args.src} -> {args.out}")
    print(f"  original:   {r['orig_size']:,} bytes")
    print(f"  compressed: {r['compressed_size']:,} bytes ({saved:.1f}% smaller)")
    print(f"  chunks:     {r['chunks']}")
    print(f"  sha256:     {r['orig_sha256']}")


def cmd_restore(args) -> None:
    r = restore_file(args.src, args.out)
    print(f"[OK] restored to {args.out}")
    print(f"  size:    {r['restored_size']:,} bytes")
    print(f"  sha256:  {r['orig_sha256']}  (verified)")


def cmd_inspect(args) -> None:
    with open(args.src, "rb") as f:
        h = read_header(f)
    print(f"version:     {h['version']}")
    print(f"original:    {h['orig_size']:,} bytes")
    print(f"chunks:      {h['chunk_count']}")
    print(f"chunk size:  {h['chunk_size']}")
    print(f"filename:    {h['manifest']['filename']}")
    print(f"sha256:      {h['orig_sha256'].hex()}")


def cmd_verify(args) -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    try:
        restore_file(args.src, tmp_path)
        print("[OK] archive verifies cleanly")
    finally:
        os.unlink(tmp_path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="akp", description="AKPack CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compress")
    c.add_argument("src"); c.add_argument("out")
    c.set_defaults(func=cmd_compress)

    r = sub.add_parser("restore")
    r.add_argument("src"); r.add_argument("out")
    r.set_defaults(func=cmd_restore)

    i = sub.add_parser("inspect")
    i.add_argument("src")
    i.set_defaults(func=cmd_inspect)

    v = sub.add_parser("verify")
    v.add_argument("src")
    v.set_defaults(func=cmd_verify)

    args = p.parse_args(argv)
    args.func(args)
    return 0


app = main

if __name__ == "__main__":
    sys.exit(main())