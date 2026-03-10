# VogueVision

> AI-powered fashion assistant that uses your camera and voice to analyze outfits and recommend clothing in real time, built with Gemini 2.5 Flash.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Camera-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-UI-FF6F00?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=flat-square&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## What it does

VogueVision lets you speak a fashion query — *"wedding attire for men"*, *"casual office look for women"* — while pointing your camera at anything. It then:

1. **Listens** to your voice query via microphone
2. **Captures** a frame from your live camera feed
3. **Analyzes** both using Google Gemini 2.5 Flash and returns a styled answer
4. **Recommends** matching outfits from a curated product database, with direct buy links

---

## Project Structure

```
VogueVision/
│
├── app.py                        # Main application — UI + camera + voice + AI
│
├── core/
│   └── recommender.py            # Clothing recommendation engine
│
├── data/
│   ├── db_products_cleaned.csv   # Cleaned product dataset (2031 items)
│   └── db_products_raw.csv       # Original raw dataset (for reference)
│
├── assets/
│   └── clothing_images/          # Product images organized by SKU
│       ├── SKU001/
│       │   ├── SKU001_1.jpg
│       │   └── SKU001_2.jpg
│       └── ...
│
├── cleaning/
│   └── clean_products.ipynb      # Data cleaning notebook (7 steps)
│
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Vision & Language | Google Gemini 2.5 Flash |
| Speech Input | SpeechRecognition + PyAudio |
| Text to Speech | pyttsx3 |
| Camera | OpenCV |
| UI | Tkinter + Pillow |
| Data | Pandas |
| Dataset | Custom CSV — 2031 products, 3 gender categories |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/VogueVision.git
cd VogueVision
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Windows PyAudio note:** If `pip install pyaudio` fails, run:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 4. Add your Gemini API key

Open `app.py` and replace the key on this line:

```python
GEMINI_API_KEY = "your-api-key-here"
```

Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Add product images

Place your clothing images inside `assets/clothing_images/` with one folder per SKU matching the `sku` column in the CSV:

```
assets/clothing_images/
└── SKU001/
    ├── SKU001_1.jpg
    └── SKU001_2.jpg
```

### 6. Run

```bash
python app.py
```

---

## How to use

1. Launch the app — your camera feed appears on the left
2. Click **◉ ASK WITH VOICE**
3. Speak your query, for example:
   - *"What should I wear to a wedding as a man?"*
   - *"Suggest a casual outfit for women"*
   - *"Office look for him"*
4. Gemini analyzes your question and the camera frame and speaks the answer
5. Matching outfits appear on the right panel — click **SHOP NOW** to open the product page

---

## Data Cleaning

The raw dataset was cleaned using `cleaning/clean_products.ipynb` which covers:

- Stripping HTML tags from descriptions
- Fixing non-ASCII / unicode characters in occasions
- Filling null values
- Dropping the all-zero MRP column
- Standardizing gender capitalization
- Splitting CamelCase concatenated occasion keywords (e.g. `WeddingSangeetMehendi` → `Wedding, Sangeet, Mehendi`)

---

## How recommendations work

1. Your voice query is stripped of stopwords and expanded using an occasion synonym map (e.g. `"wedding"` → also matches `sangeet`, `mehendi`, `haldi`, `reception`)
2. Each product row is scored against the expanded keywords using both word-level and substring matching
3. Gender is detected from your query (`men`/`women`/`unknown`) and used to filter results strictly
4. Top 6 scoring products that have local images are shown

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for full details.

In short, you are free to:
- ✅ Use this project personally or commercially
- ✅ Modify and distribute it
- ✅ Use it in private or open source projects

As long as you:
- 📌 Include the original copyright notice and license in any copy or substantial portion of the software

> **Note:** This license covers the VogueVision source code only. The product dataset (`db_products_cleaned.csv`) and clothing images belong to their respective brand owners and are not covered by this license.