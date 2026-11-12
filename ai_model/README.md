# AI model: dataset and training

Categories: plastic, paper, metal, glass, organic.

## 1. Get a dataset
Download the Kaggle **"Garbage Classification"** dataset (12 classes, ~15k images; search that title on kaggle.com) and unzip it.
It has no "organic" folder; its `biological` folder is mapped to organic. TrashNet-style folders also work, but TrashNet has no organic class,
so use the Kaggle set (or add your own `organic` images). Folders for battery, clothes, shoes and trash are ignored.

## 2. Prepare and train (PowerShell, venv active)
    pip install -r requirements-ai.txt
    python -m ai_model.prepare_dataset --src C:\path\to\garbage_dataset
    python -m ai_model.train
Check the per-category counts that prepare_dataset prints; badly unbalanced data is handled with class weights but more images help.
Training writes `ai_model/model/waste_model.keras`, `classes.json` and `metrics.json` (test accuracy, confusion matrix).
Expect minutes on GPU, longer on CPU. Reported accuracy depends on your data; read metrics.json rather than assuming.

## 3. Try it
    python -m ai_model.predict some_image.jpg
The web app loads the same model automatically. Restart the server after training.

Limits: the model recognises one dominant item per photo and always picks one of the 5 categories, so low confidence results deserve a second look.
