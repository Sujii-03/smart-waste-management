"""Maps a downloaded raw dataset into ai_model/dataset/<plastic|paper|metal|glass|organic>/.
Usage: python -m ai_model.prepare_dataset --src path/to/raw_dataset
Works with the Kaggle "Garbage Classification" (12 classes) dataset and TrashNet-style folders."""
import argparse, os, shutil, cv2

TARGET = {  # raw folder name (lowercase) -> our category
    "plastic": "plastic", "paper": "paper", "cardboard": "paper", "metal": "metal",
    "glass": "glass", "brown-glass": "glass", "green-glass": "glass", "white-glass": "glass",
    "biological": "organic", "organic": "organic",
}
EXTS = (".jpg", ".jpeg", ".png")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", default=os.path.join(os.path.dirname(__file__), "dataset"))
    a = ap.parse_args()
    counts, skipped, bad = {}, set(), 0
    for root, _, files in os.walk(a.src):
        folder = os.path.basename(root).lower()
        if not any(f.lower().endswith(EXTS) for f in files): continue
        if folder not in TARGET:
            skipped.add(folder); continue
        cat = TARGET[folder]; out = os.path.join(a.dst, cat); os.makedirs(out, exist_ok=True)
        for f in files:
            if not f.lower().endswith(EXTS): continue
            src = os.path.join(root, f)
            if cv2.imread(src) is None: bad += 1; continue  # drop unreadable/corrupt images
            shutil.copy2(src, os.path.join(out, f"{folder}_{f}"))
            counts[cat] = counts.get(cat, 0) + 1
    print("Images per category:", counts)
    print("Ignored folders (not part of our 5 categories):", sorted(skipped))
    if bad: print(f"Skipped {bad} unreadable images")
    missing = {"plastic", "paper", "metal", "glass", "organic"} - set(counts)
    if missing: print("WARNING: no images for", sorted(missing), "- training needs all 5 categories.")

if __name__ == "__main__":
    main()
