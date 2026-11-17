# Release assets

Install the authoring-only dependencies with `python -m pip install "qrcode[pil]" zxing-cpp pillow`, then run `python scripts/release_assets.py` from the root. These dependencies are not needed by the deployed API. The script requires a verified HTTPS response from the actual custom domain and decodes the PNG before copying assets.

The public interview ZIP is assembled from presentation_assets and the completed handover. site-preview.png is converted from an actual browser screenshot; it is not a rendered mock-up. Do not replace it with a local-development screenshot.
