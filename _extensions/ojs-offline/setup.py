#!/usr/bin/env python3
"""
Download Observable JS dependencies for offline use

This script downloads all required JavaScript libraries for offline Observable JS
rendering in Quarto. Run this script once after installing the extension.

Usage:
    python3 setup.py
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict, List

# Dependencies to download
# Each dependency can have "files" (required) and "optional_files" (nice to have)
DEPENDENCIES = {
    # Core Observable libraries
    "@observablehq/inputs": {
        "version": "0.10.6",
        "files": [
            "dist/inputs.min.js"
        ],
        "optional_files": [
            "dist/inputs.min.js.map"
        ]
    },
    "@observablehq/plot": {
        "version": "0.6.11",
        "files": [
            "dist/plot.umd.min.js"
        ],
        "optional_files": [
            "dist/plot.umd.min.js.map"
        ]
    },
    "@observablehq/graphviz": {
        "version": "0.2.1",
        "files": [
            "dist/graphviz.min.js"
        ]
    },
    "@observablehq/highlight.js": {
        "version": "2.0.0",
        "files": [
            "highlight.min.js"
        ]
    },
    "@observablehq/katex": {
        "version": "0.11.1",
        "files": [
            "dist/katex.min.js",
            "dist/katex.min.css"
        ]
    },
    # Data visualization
    "d3": {
        "version": "7.8.5",
        "files": [
            "dist/d3.min.js"
        ],
        "optional_files": [
            "dist/d3.min.js.map"
        ]
    },
    "vega": {
        "version": "5.22.1",
        "files": [
            "build/vega.min.js"
        ],
        "optional_files": [
            "build/vega.min.js.map"
        ]
    },
    "vega-lite": {
        "version": "5.6.0",
        "files": [
            "build/vega-lite.min.js"
        ],
        "optional_files": [
            "build/vega-lite.min.js.map"
        ]
    },
    "vega-lite-api": {
        "version": "5.0.0",
        "files": [
            "build/vega-lite-api.min.js"
        ],
        "optional_files": [
            "build/vega-lite-api.min.js.map"
        ]
    },
    # Data processing
    "arquero": {
        "version": "4.8.8",
        "files": [
            "dist/arquero.min.js"
        ],
        "optional_files": [
            "dist/arquero.min.js.map"
        ]
    },
    "apache-arrow": {
        "version": "11.0.0",
        "files": [
            "Arrow.es2015.min.js"
        ],
        "optional_files": [
            "Arrow.es2015.min.js.map"
        ]
    },
    "@duckdb/duckdb-wasm": {
        "version": "1.24.0",
        "files": [
            "dist/duckdb-mvp.wasm",
            "dist/duckdb-eh.wasm",
            "dist/duckdb-browser-mvp.worker.js",
            "dist/duckdb-browser-eh.worker.js"
        ]
    },
    "sql.js": {
        "version": "1.8.0",
        "files": [
            "dist/sql-wasm.js",
            "dist/sql-wasm.wasm"
        ]
    },
    # Utilities
    "htl": {
        "version": "0.3.1",
        "files": [
            "dist/htl.min.js"
        ],
        "optional_files": [
            "dist/htl.min.js.map"
        ]
    },
    "lodash": {
        "version": "4.17.21",
        "files": [
            "lodash.min.js"
        ]
    },
    "jszip": {
        "version": "3.10.1",
        "files": [
            "dist/jszip.min.js"
        ]
    },
    "marked": {
        "version": "0.3.12",
        "files": [
            "marked.min.js"
        ]
    },
    "topojson-client": {
        "version": "3.1.0",
        "files": [
            "dist/topojson-client.min.js"
        ]
    },
    "exceljs": {
        "version": "4.3.0",
        "files": [
            "dist/exceljs.min.js"
        ]
    },
    "leaflet": {
        "version": "1.9.4",
        "files": [
            "dist/leaflet.js",
            "dist/leaflet.css"
        ]
    },
    "mermaid": {
        "version": "10.6.1",
        "files": [
            "dist/mermaid.min.js"
        ],
        "optional_files": [
            "dist/mermaid.min.js.map"
        ]
    }
}


def load_registry_config(config_file: Path = None) -> Dict:
    """Load registry configuration from file"""
    if config_file and config_file.exists():
        with open(config_file) as f:
            return json.load(f)

    # Try default config file location
    default_config = Path(__file__).parent / "registry-config.json"
    if default_config.exists():
        with open(default_config) as f:
            return json.load(f)

    return {}


def validate_registry_url(url: str) -> bool:
    """Validate that the registry URL is properly formatted"""
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme in ['http', 'https']:
            print(f"⚠ Warning: Registry URL should use http or https")
            return False
        if not parsed.netloc:
            print(f"⚠ Warning: Invalid registry URL: {url}")
            return False
        return True
    except Exception as e:
        print(f"⚠ Warning: Could not parse registry URL: {e}")
        return False


class DependencyDownloader:
    def __init__(self, base_dir: Path, registry_url: str = None, timeout: int = 30):
        self.base_dir = base_dir
        self.libs_dir = base_dir / "resources" / "libs"
        self.dependency_map = {}
        self.failed_downloads = []
        self.failed_optional = []

        # Use custom registry or default
        self.registry_url = registry_url or "https://cdn.jsdelivr.net/npm"
        self.timeout = timeout

        # Validate registry URL
        if not validate_registry_url(self.registry_url):
            print(f"⚠ Warning: Proceeding with potentially invalid registry URL")


    def download_file(self, url: str, local_path: Path, optional: bool = False) -> bool:
        """Download a file from URL to local path"""
        try:
            print(f"  Downloading: {url}")
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Create request with user agent
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Quarto-OJS-Offline-Extension/1.0'}
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read()
                with open(local_path, 'wb') as f:
                    f.write(content)

            file_size = len(content) / 1024  # KB
            print(f"    ✓ Saved to: {local_path.relative_to(self.base_dir)} ({file_size:.1f} KB)")
            return True

        except urllib.error.HTTPError as e:
            if optional:
                print(f"    ⊘ Optional file not found (skipping)")
                self.failed_optional.append((url, str(e)))
            else:
                print(f"    ✗ HTTP Error {e.code}: {e.reason}")
                self.failed_downloads.append((url, str(e)))
            return False
        except urllib.error.URLError as e:
            if optional:
                print(f"    ⊘ Optional file unavailable (skipping)")
                self.failed_optional.append((url, str(e)))
            else:
                print(f"    ✗ URL Error: {e.reason}")
                self.failed_downloads.append((url, str(e)))
            return False
        except Exception as e:
            if optional:
                print(f"    ⊘ Optional file error (skipping)")
                self.failed_optional.append((url, str(e)))
            else:
                print(f"    ✗ Error: {e}")
                self.failed_downloads.append((url, str(e)))
            return False

    def download_package(self, name: str, config: Dict) -> None:
        """Download all files for a package"""
        version = config["version"]
        files = config.get("files", [])
        optional_files = config.get("optional_files", [])

        print(f"\n📦 {name}@{version}")

        # Download required files
        for file_path in files:
            # Construct registry URL
            url = f"{self.registry_url}/{name}@{version}/{file_path}"

            # Construct local path
            local_path = self.libs_dir / f"{name}@{version}" / file_path

            # Download file
            if self.download_file(url, local_path, optional=False):
                # Add to dependency map
                # Map both with and without the package version for flexibility
                map_key = f"{name}@{version}/{file_path}"
                # Make path relative to the HTML document's libs directory
                map_value = f"ojs-offline-libs/{name}@{version}/{file_path}"
                self.dependency_map[map_key] = map_value

                # Also add base package mapping (points to main file)
                if file_path == files[0]:  # First file is the main entry
                    self.dependency_map[f"{name}@{version}"] = map_value
                    self.dependency_map[name] = map_value

        # Download optional files (like source maps)
        for file_path in optional_files:
            url = f"{self.registry_url}/{name}@{version}/{file_path}"
            local_path = self.libs_dir / f"{name}@{version}" / file_path

            if self.download_file(url, local_path, optional=True):
                # Add to dependency map if downloaded successfully
                map_key = f"{name}@{version}/{file_path}"
                map_value = f"ojs-offline-libs/{name}@{version}/{file_path}"
                self.dependency_map[map_key] = map_value

    def save_dependency_map(self) -> None:
        """Save dependency map to JSON file"""
        map_path = self.base_dir / "resources" / "dependency-map.json"
        print(f"\n💾 Saving dependency map to: {map_path.relative_to(self.base_dir)}")

        with open(map_path, 'w') as f:
            json.dump(self.dependency_map, f, indent=2, sort_keys=True)

        print(f"   ✓ Saved {len(self.dependency_map)} entries")

    def print_summary(self) -> None:
        """Print download summary"""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        total_size = 0
        for root, dirs, files in os.walk(self.libs_dir):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size

        print(f"✓ Total packages: {len(DEPENDENCIES)}")
        print(f"✓ Total files: {len(self.dependency_map) // 3}")  # Rough estimate
        print(f"✓ Total size: {total_size / (1024*1024):.1f} MB")

        if self.failed_downloads:
            print(f"\n⚠ FAILED REQUIRED DOWNLOADS: {len(self.failed_downloads)}")
            for url, error in self.failed_downloads:
                print(f"  - {url}")
                print(f"    Error: {error}")
        else:
            print("\n✓ All required files downloaded successfully!")

        if self.failed_optional:
            print(f"\nℹ Skipped optional files: {len(self.failed_optional)} (source maps)")
            print("  These are debug files - not needed for functionality")

    def run(self) -> int:
        """Run the download process"""
        print("="*60)
        print("Quarto OJS Offline - Dependency Downloader")
        print("="*60)
        print(f"Target directory: {self.base_dir}")
        print(f"Libraries directory: {self.libs_dir}")
        print(f"Registry: {self.registry_url}")
        print(f"Timeout: {self.timeout}s")
        print()

        # Create directories
        self.libs_dir.mkdir(parents=True, exist_ok=True)

        # Download all packages
        for name, config in DEPENDENCIES.items():
            self.download_package(name, config)

        # Save dependency map
        self.save_dependency_map()

        # Print summary
        self.print_summary()

        # Return exit code
        return 1 if self.failed_downloads else 0


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Download Observable JS dependencies for offline use"
    )
    parser.add_argument(
        '-r', '--registry',
        help='Custom npm registry URL (default: https://cdn.jsdelivr.net/npm)',
        default=None
    )
    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Path to registry configuration file',
        default=None
    )
    parser.add_argument(
        '--timeout',
        type=int,
        help='Download timeout in seconds (default: 30)',
        default=30
    )

    args = parser.parse_args()

    # Load configuration with priority: CLI > ENV > Config file > Default
    config = load_registry_config(args.config)

    registry_url = (
        args.registry or
        os.environ.get('NPM_REGISTRY') or
        config.get('registry') or
        "https://cdn.jsdelivr.net/npm"
    )

    timeout = (
        args.timeout if args.timeout != 30 else
        int(os.environ.get('NPM_TIMEOUT', config.get('timeout', 30)))
    )

    # Determine base directory (where this script is located)
    script_dir = Path(__file__).parent.resolve()

    # Run downloader with custom registry
    downloader = DependencyDownloader(script_dir, registry_url, timeout)
    exit_code = downloader.run()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
