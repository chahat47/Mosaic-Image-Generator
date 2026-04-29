# 🖼️ Photo Mosaic Generator

A desktop Python application that transforms any image into a stunning photo mosaic — composed entirely of smaller tile images. Features a clean **tkinter GUI**, integrated tile downloader, and fast mosaic rendering powered by **Pillow** and **NumPy**.

---

## ✨ Features

- **Mosaic Generation** — Reconstruct a target image using a library of tile images matched by average color
- **Integrated Tile Downloader** — Download and manage tile datasets directly from the GUI, no manual setup needed
- **tkinter GUI** — Intuitive desktop interface for loading images, configuring settings, and previewing results
- **NumPy-Accelerated Matching** — Fast average-color computation and nearest-neighbor tile matching using vectorized operations
- **Configurable Grid Size** — Control tile resolution to balance detail vs. performance
- **Export Support** — Save the final mosaic as a high-quality image file

---

## 🛠️ Tech Stack

| Component        | Technology              |
|------------------|-------------------------|
| GUI Framework    | `tkinter`               |
| Image Processing | `Pillow (PIL)`          |
| Numerical Ops    | `NumPy`                 |
| Tile Downloading | `requests` / `urllib`   |
| Language         | Python 3.x              |

---

## 📁 Project Structure

```
photo-mosaic-generator/
│
├── main.py                 # Application entry point
├── mosaic.py               # Core mosaic generation logic
├── tile_downloader.py      # Tile image fetching and management
├── gui.py                  # tkinter UI components and layout
├── utils.py                # Helper functions (color averaging, resizing, etc.)
│
├── tiles/                  # Directory for downloaded/stored tile images
├── output/                 # Generated mosaic output images
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/photo-mosaic-generator.git
cd photo-mosaic-generator

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
python main.py
```

---

## 🧩 How It Works

1. **Load a target image** — The image you want to recreate as a mosaic
2. **Build a tile library** — Use the integrated downloader or point to a local folder of images
3. **Precompute tile colors** — Each tile's average RGB color is computed and stored
4. **Grid division** — The target image is divided into an N×N grid of cells
5. **Color matching** — Each cell's average color is compared against the tile library; the closest match (by Euclidean distance in RGB space) is selected
6. **Assembly** — Matched tiles are stitched together to form the final mosaic
7. **Export** — Save the result to the `output/` directory

---

## ⚙️ Configuration

| Setting         | Description                              | Default   |
|-----------------|------------------------------------------|-----------|
| Tile Size       | Pixel dimensions of each tile cell       | `30x30`   |
| Grid Density    | Number of tiles across width/height      | Auto      |
| Reuse Tiles     | Allow a tile to be used multiple times   | `True`    |
| Output Format   | File format for saved mosaic             | `PNG`     |

---

## 📦 Requirements

```
Pillow>=9.0.0
numpy>=1.23.0
requests>=2.28.0
```

---

## 🖥️ Screenshots

> _Add screenshots of the GUI and example mosaic outputs here_

---

## 🔮 Planned Improvements

- [ ] Multi-threaded tile matching for faster generation on large images
- [ ] Tile deduplication toggle to force unique tile placement
- [ ] Progress bar with real-time mosaic preview
- [ ] Support for animated GIF mosaics
- [ ] Web-based version using Flask or Streamlit

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [NumPy](https://numpy.org/)
- Inspired by the classic photomosaic technique popularized by Robert Silvers
