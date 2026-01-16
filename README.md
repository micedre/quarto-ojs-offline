# OJS Offline - Quarto Extension

Render Quarto Observable JS documents completely offline by bundling all CDN dependencies locally.

## Problem

By default, Quarto documents with Observable JS require internet connectivity to load JavaScript libraries from the jsdelivr CDN. This extension solves that problem by:

1. Bundling all required JavaScript libraries locally
2. Intercepting module loading to use local files instead of CDN
3. Supporting the full Observable JS ecosystem (d3, arquero, plot, etc.)

## Features

- Complete offline support (no network required after setup)
- Supports all major Observable JS libraries
- Faster page loads (no CDN latency)
- Works in air-gapped environments
- Version-locked dependencies for reproducibility

## Installation

### Option 1: From GitHub (recommended)

```bash
quarto add yourusername/quarto-ojs-offline
```

### Option 2: Manual installation

```bash
# Clone or copy the extension to your project
mkdir -p _extensions
cp -r path/to/ojs-offline _extensions/
```

## Setup

After installation, you must download the JavaScript dependencies:

```bash
cd _extensions/ojs-offline
python3 setup.py
```

This will:
- Download ~20 JavaScript libraries from jsdelivr CDN (~15-20 MB)
- Create the `resources/libs/` directory with all dependencies
- Generate `resources/dependency-map.json` with path mappings

The setup only needs to be run once (or when updating dependencies).

## Usage

### In a Quarto document

Add the filter to your document's YAML frontmatter:

```yaml
---
title: "My Offline Observable Document"
format:
  html:
    filters:
      - ojs-offline
---
```

Then write Observable JS code as usual:

````markdown
```{ojs}
d3 = require("d3@7")
data = [1, 2, 3, 4, 5]
d3.sum(data)
```
````

### Using the custom format

Alternatively, use the pre-configured format:

```yaml
---
title: "My Offline Observable Document"
format: ojs-offline-html
---
```

## Supported Libraries

The extension bundles the following libraries:

### Core Observable
- @observablehq/inputs - Form inputs and controls
- @observablehq/plot - Observable Plot visualization library
- @observablehq/graphviz - Graphviz rendering
- @observablehq/highlight.js - Syntax highlighting
- @observablehq/katex - Math rendering

### Data Visualization
- d3 - D3.js visualization library
- vega - Vega visualization grammar
- vega-lite - Vega-Lite declarative visualization
- vega-lite-api - JavaScript API for Vega-Lite

### Data Processing
- arquero - Data wrangling and analysis
- apache-arrow - Apache Arrow for efficient data
- @duckdb/duckdb-wasm - DuckDB in the browser
- sql.js - SQLite compiled to WebAssembly

### Utilities
- htl - Hypertext literal
- lodash - Utility functions
- jszip - Create and read ZIP files
- topojson-client - TopoJSON utilities
- exceljs - Excel file handling
- leaflet - Interactive maps
- mermaid - Diagrams and flowcharts

## How It Works

1. **Lua Filter** (`ojs-offline.lua`): Injects an inline interceptor script into the HTML `<head>`
2. **Interceptor Script**: Overrides `window.fetch` and `document.createElement` to intercept CDN requests
3. **Dependency Map** (`dependency-map.json`): Maps package identifiers to local file paths
4. **Bundled Libraries** (`resources/libs/`): All JavaScript libraries stored locally

The inline interceptor script loads **before** Quarto's OJS runtime module (which is deferred), allowing it to intercept all CDN requests for npm packages.

## Examples

### Simple D3 visualization

```yaml
---
title: "D3 Bar Chart"
format:
  html:
    filters:
      - ojs-offline
---
```

````markdown
```{ojs}
d3 = require("d3@7")
data = [30, 86, 168, 281, 303, 365]

svg = {
  const width = 640;
  const height = 400;
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

  svg.selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", (d, i) => i * 100)
    .attr("y", d => height - d)
    .attr("width", 95)
    .attr("height", d => d)
    .attr("fill", "steelblue");

  return svg.node();
}
```
````

### Observable Plot

````markdown
```{ojs}
Plot = require("@observablehq/plot")
d3 = require("d3")

penguins = d3.csv("penguins.csv", d3.autoType)

Plot.plot({
  marks: [
    Plot.dot(penguins, {
      x: "flipper_length_mm",
      y: "body_mass_g",
      fill: "species"
    })
  ]
})
```
````

### Arquero data wrangling

````markdown
```{ojs}
aq = require("arquero")

table = aq.table({
  name: ["Alice", "Bob", "Charlie"],
  age: [25, 30, 35],
  city: ["NYC", "LA", "Chicago"]
})

table.filter(d => d.age > 28).view()
```
````

## Troubleshooting

### Dependencies not loading

If you see console errors about missing modules:

1. Verify setup.py completed successfully: `python3 setup.py`
2. Check that `resources/libs/` directory exists and contains packages
3. Check that `resources/dependency-map.json` was generated
4. Look for errors in browser console (press F12)

### Check interceptor status

Open the browser console (F12) to see if the interceptor loaded:

```
[OJS Offline] Interceptor loaded with 90 dependency mappings
```

If you don't see this message, the filter may not be applied correctly.

### Module not found

If a specific module isn't loading:

1. Check if it's in the dependency list in `setup.py`
2. Verify the file was downloaded: `ls resources/libs/<package-name>@<version>`
3. Check the dependency map: `cat resources/dependency-map.json | grep <package-name>`

### Still requires internet

The extension only works after setup.py has been run. If you're still seeing network requests:

1. Clear browser cache
2. Check that the filter is applied in your YAML frontmatter
3. Verify the Lua filter is being loaded (check Quarto output)

## Limitations

- **Repository size**: Adds ~15-20 MB to your project
- **Initial setup**: Requires running setup.py with internet connection
- **Version locked**: Dependencies are at fixed versions (can be updated in setup.py)
- **WASM complexity**: Some libraries (DuckDB, sql.js) require WebAssembly files
- **ESM modules**: Apache Arrow and DuckDB use modern ES modules

## Updating Dependencies

To update to newer versions:

1. Edit `setup.py` and change version numbers
2. Run `python3 setup.py` again
3. Test your documents with the new versions

## Technical Details

### Script Loading Order

The interceptor must load before Quarto's OJS runtime. This is achieved by:
- Injecting an inline `<script>` tag in the HTML `<head>` using `quarto.doc.include_text("in-header", ...)`
- Quarto's OJS runtime uses `type="module"` which is always deferred
- Regular inline scripts execute immediately when parsed, before deferred modules

### Path Resolution

Libraries are stored in:
```
site_libs/
  quarto-contrib/
    ojs-offline-libs-1.0.0/
      libs/
        <package>@<version>/
          <files>
```

The dependency map is embedded in the inline script with paths pointing to these resources.

### Module Formats

The extension supports:
- **UMD modules**: Loaded via script injection
- **ES modules**: Loaded via dynamic `import()`
- **WASM**: WebAssembly files with proper initialization

## Contributing

Contributions are welcome! To add a new library:

1. Add it to `DEPENDENCIES` in `setup.py`
2. Run `python3 setup.py` to download
3. Test with a Quarto document
4. Submit a pull request

## License

MIT License

## Acknowledgments

- Built for [Quarto](https://quarto.org/)
- Inspired by the Observable team's amazing work on [Observable JS](https://observablehq.com/@observablehq/observable-javascript)
- Uses [jsdelivr](https://www.jsdelivr.com/) CDN for downloading dependencies
