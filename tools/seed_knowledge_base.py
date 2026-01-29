#!/usr/bin/env python3
"""
Knowledge Base Seeder for AI Integrator
========================================

Seeds the ai-integrator knowledge base from luthiers-toolbox catalogs.

Sources:
- instrument_model_registry.json (19 models)
- body/catalog.json (16 body outlines)
- rosette_pattern_catalog.json (24 patterns)
- vision/vocabulary.py (6 vocabulary lists)

Usage:
    python tools/seed_knowledge_base.py --toolbox-path /path/to/luthiers-toolbox

Output:
    knowledge/
    ├── lutherie/
    │   ├── instruments.json      # Instrument models
    │   ├── body_outlines.json    # Body geometry catalog
    │   ├── woods.json            # Tonewood vocabulary
    │   └── components.json       # Component vocabulary
    ├── styles/
    │   ├── finishes.json         # Finish types
    │   ├── eras.json             # Style eras
    │   └── photography.json      # Photography styles
    ├── patterns/
    │   └── rosettes.json         # Rosette patterns
    └── manifest.json             # Seed manifest with provenance
"""

from __future__ import annotations

import json
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default paths
DEFAULT_TOOLBOX_PATH = Path(__file__).parent.parent.parent / "luthiers-toolbox"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if not found."""
    if not path.exists():
        print(f"  WARN: File not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_instruments(toolbox_path: Path) -> Dict[str, Any]:
    """Extract instrument models from registry."""
    registry_path = toolbox_path / "services/api/app/instrument_geometry/instrument_model_registry.json"
    data = load_json(registry_path)

    if not data:
        return {"models": [], "source": str(registry_path), "error": "not_found"}

    models = []
    for model_id, info in data.get("models", {}).items():
        models.append({
            "id": model_id,
            "display_name": info.get("display_name", model_id),
            "category": info.get("category", "unknown"),
            "scale_length_mm": info.get("scale_length_mm"),
            "fret_count": info.get("fret_count"),
            "string_count": info.get("string_count"),
            "manufacturer": info.get("manufacturer"),
            "year_introduced": info.get("year_introduced"),
            "status": info.get("status", "STUB"),
            "description": info.get("description", ""),
        })

    return {
        "models": models,
        "count": len(models),
        "source": str(registry_path),
        "categories": list(set(m["category"] for m in models)),
    }


def extract_body_outlines(toolbox_path: Path) -> Dict[str, Any]:
    """Extract body outline catalog."""
    catalog_path = toolbox_path / "services/api/app/instrument_geometry/body/catalog.json"
    data = load_json(catalog_path)

    if not data:
        return {"bodies": [], "source": str(catalog_path), "error": "not_found"}

    bodies = []
    for body_id, info in data.get("bodies", {}).items():
        bodies.append({
            "id": body_id,
            "name": info.get("name", body_id),
            "category": info.get("category", "unknown"),
            "dimensions_mm": info.get("dimensions_mm", {}),
            "points": info.get("points", 0),
            "dxf": info.get("dxf"),
            "source": info.get("source", ""),
        })

    return {
        "bodies": bodies,
        "count": len(bodies),
        "source": str(catalog_path),
        "categories": data.get("categories", {}),
    }


def extract_rosette_patterns(toolbox_path: Path) -> Dict[str, Any]:
    """Extract rosette pattern catalog."""
    catalog_path = toolbox_path / "services/api/app/data/rosette_pattern_catalog.json"
    data = load_json(catalog_path)

    if not data:
        return {"patterns": [], "source": str(catalog_path), "error": "not_found"}

    patterns = []
    for category, pattern_list in data.get("categories", {}).items():
        for pattern in pattern_list:
            patterns.append({
                "id": pattern.get("id"),
                "name": pattern.get("name"),
                "category": category,
                "rows": pattern.get("rows"),
                "columns": pattern.get("columns"),
                "materials": pattern.get("materials", []),
                "dimensions": pattern.get("dimensions", {}),
                "notes": pattern.get("notes", ""),
            })

    return {
        "patterns": patterns,
        "count": len(patterns),
        "source": str(catalog_path),
        "categories": list(data.get("categories", {}).keys()),
    }


def extract_vocabulary(toolbox_path: Path) -> Dict[str, Any]:
    """Extract vision vocabulary."""
    vocab_path = toolbox_path / "services/api/app/vision/vocabulary.py"

    if not vocab_path.exists():
        return {"error": "not_found", "source": str(vocab_path)}

    # Parse vocabulary from Python file
    vocab = {
        "body_shapes": [],
        "finishes": [],
        "woods": [],
        "hardware": [],
        "inlays": [],
        "photography_styles": [],
    }

    with open(vocab_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract lists using simple parsing
    import re
    for key in vocab.keys():
        # Match VARIABLE: List[str] = [...]
        pattern = rf'{key.upper()}: List\[str\] = \[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            items_str = match.group(1)
            items = re.findall(r'"([^"]+)"', items_str)
            vocab[key] = items

    return {
        "vocabulary": vocab,
        "source": str(vocab_path),
        "counts": {k: len(v) for k, v in vocab.items()},
    }


def create_knowledge_structure(output_dir: Path) -> None:
    """Create knowledge base directory structure."""
    dirs = [
        output_dir / "lutherie",
        output_dir / "styles",
        output_dir / "patterns",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Dict[str, Any]) -> str:
    """Write JSON file and return sha256."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def seed_knowledge_base(toolbox_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Main seeding function.

    Extracts data from luthiers-toolbox and writes to ai-integrator knowledge base.
    """
    print(f"Seeding knowledge base from: {toolbox_path}")
    print(f"Output directory: {output_dir}")
    print()

    create_knowledge_structure(output_dir)

    manifest = {
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "source": str(toolbox_path),
        "files": {},
    }

    # Extract instruments
    print("Extracting instrument models...")
    instruments = extract_instruments(toolbox_path)
    path = output_dir / "lutherie" / "instruments.json"
    sha = write_json(path, instruments)
    manifest["files"]["instruments"] = {"path": str(path), "sha256": sha, "count": instruments.get("count", 0)}
    print(f"  -> {instruments.get('count', 0)} models written to {path.name}")

    # Extract body outlines
    print("Extracting body outlines...")
    bodies = extract_body_outlines(toolbox_path)
    path = output_dir / "lutherie" / "body_outlines.json"
    sha = write_json(path, bodies)
    manifest["files"]["body_outlines"] = {"path": str(path), "sha256": sha, "count": bodies.get("count", 0)}
    print(f"  -> {bodies.get('count', 0)} bodies written to {path.name}")

    # Extract rosette patterns
    print("Extracting rosette patterns...")
    rosettes = extract_rosette_patterns(toolbox_path)
    path = output_dir / "patterns" / "rosettes.json"
    sha = write_json(path, rosettes)
    manifest["files"]["rosettes"] = {"path": str(path), "sha256": sha, "count": rosettes.get("count", 0)}
    print(f"  -> {rosettes.get('count', 0)} patterns written to {path.name}")

    # Extract vocabulary
    print("Extracting vision vocabulary...")
    vocab = extract_vocabulary(toolbox_path)

    # Woods
    woods_data = {
        "woods": vocab.get("vocabulary", {}).get("woods", []),
        "source": vocab.get("source"),
        "description": "Tonewood types for guitar construction",
    }
    path = output_dir / "lutherie" / "woods.json"
    sha = write_json(path, woods_data)
    manifest["files"]["woods"] = {"path": str(path), "sha256": sha, "count": len(woods_data["woods"])}

    # Components (hardware + inlays)
    components_data = {
        "hardware": vocab.get("vocabulary", {}).get("hardware", []),
        "inlays": vocab.get("vocabulary", {}).get("inlays", []),
        "body_shapes": vocab.get("vocabulary", {}).get("body_shapes", []),
        "source": vocab.get("source"),
    }
    path = output_dir / "lutherie" / "components.json"
    sha = write_json(path, components_data)
    manifest["files"]["components"] = {"path": str(path), "sha256": sha}

    # Finishes
    finishes_data = {
        "finishes": vocab.get("vocabulary", {}).get("finishes", []),
        "source": vocab.get("source"),
    }
    path = output_dir / "styles" / "finishes.json"
    sha = write_json(path, finishes_data)
    manifest["files"]["finishes"] = {"path": str(path), "sha256": sha, "count": len(finishes_data["finishes"])}

    # Photography styles
    photo_data = {
        "photography_styles": vocab.get("vocabulary", {}).get("photography_styles", []),
        "source": vocab.get("source"),
    }
    path = output_dir / "styles" / "photography.json"
    sha = write_json(path, photo_data)
    manifest["files"]["photography"] = {"path": str(path), "sha256": sha, "count": len(photo_data["photography_styles"])}

    print(f"  -> Vocabulary split into woods, components, finishes, photography")

    # Write manifest
    print()
    print("Writing manifest...")
    manifest_path = output_dir / "manifest.json"
    write_json(manifest_path, manifest)
    print(f"  -> Manifest written to {manifest_path.name}")

    # Summary
    print()
    print("=" * 60)
    print("KNOWLEDGE BASE SEEDING COMPLETE")
    print("=" * 60)
    print(f"  Instruments:  {manifest['files'].get('instruments', {}).get('count', 0)}")
    print(f"  Body outlines: {manifest['files'].get('body_outlines', {}).get('count', 0)}")
    print(f"  Rosettes:     {manifest['files'].get('rosettes', {}).get('count', 0)}")
    print(f"  Woods:        {manifest['files'].get('woods', {}).get('count', 0)}")
    print(f"  Finishes:     {manifest['files'].get('finishes', {}).get('count', 0)}")
    print(f"  Photo styles: {manifest['files'].get('photography', {}).get('count', 0)}")
    print()

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Seed ai-integrator knowledge base from luthiers-toolbox")
    parser.add_argument(
        "--toolbox-path",
        type=Path,
        default=DEFAULT_TOOLBOX_PATH,
        help="Path to luthiers-toolbox repository",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for knowledge base",
    )
    args = parser.parse_args()

    if not args.toolbox_path.exists():
        print(f"ERROR: Toolbox path not found: {args.toolbox_path}")
        print("Use --toolbox-path to specify the luthiers-toolbox location")
        return 1

    seed_knowledge_base(args.toolbox_path, args.output_dir)
    return 0


if __name__ == "__main__":
    exit(main())
