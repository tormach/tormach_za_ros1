# Development scripts
This directory contains scripts useful during development.

## Optimize PNG icons
The `optimize_pngs.sh` compresses all png icons of the UI to reduce the file size by about 20-30%.

Requires the optipng tool: `sudo apt install optipng`

## Convert SVG icons to PNG
The `convert_svgs.sh` converts SVG icons to PNG icons to decrease loading time.

Requires the librsvg tools: `sudo apt install librsvg2-bin`
