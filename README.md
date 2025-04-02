# Syncthing Overlay

A lightweight Python application that displays Syncthing folder and device statuses in a semi-transparent, draggable overlay.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/MangaD/syncthing-overlay.git
   cd syncthing-overlay
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `config.ini` file:
   ```
   [syncthing]
   api_key = your-syncthing-api-key
   ```
4. Run the script:
   ```bash
   python syncthing_overlay.py
   ```

## Releases
Executables are built automatically via GitHub Actions and attached to releases.
