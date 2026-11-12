"""Transfer-learning trainer (MobileNetV2, ImageNet weights).
Usage: python -m ai_model.train [--epochs 12] [--finetune-epochs 8]
Saves ai_model/model/waste_model.keras, classes.json and metrics.json.
The saved model takes raw RGB pixels (0-255) at 224x224; preprocessing is inside the model."""
import argparse, json, os
import numpy as np
import tensorflow as tf

HERE = os.path.dirname(__file__)
DATA, OUT = os.path.join(HERE, "dataset"), os.path.join(HERE, "model")
SIZE, SEED = (224, 224), 42

def build(n):
    aug = tf.keras.Sequential([tf.keras.layers.RandomFlip("horizontal"), tf.keras.layers.RandomRotation(0.1),
                               tf.keras.layers.RandomZoom(0.15), tf.keras.layers.RandomContrast(0.15)])
    base = tf.keras.applications.MobileNetV2(input_shape=SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False
    inp = tf.keras.Input(SIZE + (3,))
    x = aug(inp)  # augmentation is inactive at inference
    x = tf.keras.layers.Rescaling(1 / 127.5, offset=-1)(x)  # == MobileNetV2 preprocess_input
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    out = tf.keras.layers.Dense(n, activation="softmax")(x)
    return tf.keras.Model(inp, out), base

def compile_(m, lr):
    m.compile(tf.keras.optimizers.Adam(lr), "sparse_categorical_crossentropy", metrics=["accuracy"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--finetune-epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args()
    if not os.path.isdir(DATA): raise SystemExit("Dataset missing. See ai_model/README.md")

    full = tf.keras.utils.image_dataset_from_directory(DATA, image_size=SIZE, batch_size=a.batch,
                                                       shuffle=True, seed=SEED, label_mode="int")
    classes = full.class_names
    if len(classes) < 2: raise SystemExit("Need at least 2 category folders in dataset/")
    # 70 / 15 / 15 split; the test set is never used for training or model selection
    train, rest = tf.keras.utils.split_dataset(full, left_size=0.7, seed=SEED)
    val, test = tf.keras.utils.split_dataset(rest, left_size=0.5, seed=SEED)
    labels = np.concatenate([y.numpy() for _, y in train])
    counts = np.bincount(labels, minlength=len(classes))
    cw = {i: len(labels) / (len(classes) * max(c, 1)) for i, c in enumerate(counts)}  # handle imbalance
    AUTO = tf.data.AUTOTUNE
    train, val, test = (d.cache().prefetch(AUTO) for d in (train, val, test))

    model, base = build(len(classes))
    cb = [tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True, monitor="val_accuracy")]
    compile_(model, 1e-3); model.fit(train, validation_data=val, epochs=a.epochs, class_weight=cw, callbacks=cb)
    base.trainable = True  # fine-tune the top of the backbone at a low learning rate
    for l in base.layers[:-30]: l.trainable = False
    compile_(model, 1e-5); model.fit(train, validation_data=val, epochs=a.finetune_epochs, class_weight=cw, callbacks=cb)

    y_true = np.concatenate([y.numpy() for _, y in test])
    y_pred = np.argmax(model.predict(test, verbose=0), axis=1)
    cm = tf.math.confusion_matrix(y_true, y_pred, num_classes=len(classes)).numpy()
    acc = float((y_true == y_pred).mean())
    print(f"\nTEST ACCURACY: {acc:.3f}\nClasses: {classes}\nConfusion matrix (rows=true):\n{cm}")
    os.makedirs(OUT, exist_ok=True)
    model.save(os.path.join(OUT, "waste_model.keras"))
    json.dump(classes, open(os.path.join(OUT, "classes.json"), "w"))
    json.dump({"test_accuracy": acc, "confusion_matrix": cm.tolist(), "classes": classes,
               "train_images_per_class": counts.tolist()}, open(os.path.join(OUT, "metrics.json"), "w"), indent=2)

if __name__ == "__main__":
    main()
