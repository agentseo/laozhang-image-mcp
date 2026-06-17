#!/usr/bin/env python3
"""MCP server for laozhang.ai image generation (OpenAI-compatible).

Tools:
  - generate_image: text -> image (gpt-image-2-vip)
  - edit_image:     image + prompt -> image

Config via environment:
  LAOZHANG_API_KEY   (required)  your laozhang.ai key
  LAOZHANG_BASE_URL  default https://api.laozhang.ai/v1
  LAOZHANG_MODEL     default gpt-image-2-vip
  LAOZHANG_OUT_DIR   default ./laozhang-images  (where PNGs are saved)
"""

import base64
import os
import time
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_KEY = os.environ.get("LAOZHANG_API_KEY", "")
BASE_URL = os.environ.get("LAOZHANG_BASE_URL", "https://api.laozhang.ai/v1").rstrip("/")
MODEL = os.environ.get("LAOZHANG_MODEL", "gpt-image-2-vip")
OUT_DIR = Path(os.environ.get("LAOZHANG_OUT_DIR", "laozhang-images"))

# Convenient size presets. laozhang/OpenAI accept explicit WxH or "auto".
# 1K/2K/4K map to common square tiers; we also pass through any raw "WxH".
SIZE_PRESETS = {
    "1k": "1024x1024",
    "2k": "2048x2048",
    "4k": "4096x4096",
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "auto": "auto",
}

mcp = FastMCP("laozhang-image")


def _resolve_size(size: str) -> str:
    return SIZE_PRESETS.get(size.strip().lower(), size.strip())


def _save_png(data: bytes, prefix: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # time.time() is fine here (server runtime, not a workflow script)
    name = f"{prefix}-{int(time.time() * 1000)}.png"
    path = OUT_DIR / name
    path.write_bytes(data)
    return path.resolve()


def _extract_image(item: dict, client: httpx.Client) -> tuple[bytes, Optional[str]]:
    """Return (png_bytes, source_url|None) from one data[] entry."""
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"]), None
    url = item.get("url")
    if url:
        r = client.get(url, timeout=120)
        r.raise_for_status()
        return r.content, url
    raise RuntimeError(f"No image in response item: {item}")


def _require_key() -> None:
    if not API_KEY:
        raise RuntimeError("LAOZHANG_API_KEY is not set in the environment.")


@mcp.tool()
def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "auto",
    n: int = 1,
) -> str:
    """Generate image(s) from a text prompt via laozhang.ai.

    Args:
        prompt: Text description of the image.
        size: "1k"/"2k"/"4k", "square"/"landscape"/"portrait", "auto",
              or explicit like "1536x1024".
        quality: low | medium | high | auto.
        n: number of images (1-4).
    Returns: human-readable lines with saved file path(s) and source URL(s).
    """
    _require_key()
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": max(1, min(int(n), 4)),
        "size": _resolve_size(size),
        "quality": quality,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/images/generations", json=payload, headers=headers, timeout=300
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API {resp.status_code}: {resp.text[:800]}")
        data = resp.json().get("data", [])
        if not data:
            raise RuntimeError(f"Empty data in response: {resp.text[:800]}")
        out = []
        for i, item in enumerate(data):
            png, url = _extract_image(item, client)
            path = _save_png(png, "gen")
            out.append(
                f"#{i + 1} saved: {path}" + (f"\n     url: {url}" if url else "")
            )
    return "\n".join(out)


@mcp.tool()
def edit_image(
    image_path: str,
    prompt: str,
    size: str = "auto",
    mask_path: Optional[str] = None,
) -> str:
    """Edit an existing image with a prompt (image -> image) via laozhang.ai.

    Args:
        image_path: Absolute path to the source PNG/JPG to edit.
        prompt: Instruction describing the desired change.
        size: "1k"/"2k"/"4k", "auto", or explicit "WxH".
        mask_path: Optional PNG mask (transparent = edit area).
    Returns: saved file path and source URL.
    """
    _require_key()
    src = Path(image_path)
    if not src.is_file():
        raise RuntimeError(f"image_path not found: {image_path}")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {"model": MODEL, "prompt": prompt, "size": _resolve_size(size), "n": "1"}
    files = {"image": (src.name, src.read_bytes(), "application/octet-stream")}
    if mask_path:
        m = Path(mask_path)
        if not m.is_file():
            raise RuntimeError(f"mask_path not found: {mask_path}")
        files["mask"] = (m.name, m.read_bytes(), "application/octet-stream")

    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/images/edits",
            data=data,
            files=files,
            headers=headers,
            timeout=300,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API {resp.status_code}: {resp.text[:800]}")
        items = resp.json().get("data", [])
        if not items:
            raise RuntimeError(f"Empty data in response: {resp.text[:800]}")
        png, url = _extract_image(items[0], client)
        path = _save_png(png, "edit")
    return f"saved: {path}" + (f"\nurl: {url}" if url else "")


if __name__ == "__main__":
    mcp.run()
