from io import BytesIO
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from PIL import Image
import numpy as np

def identify_image(uploaded_file):

    def process_image(image_bytes):
        img = Image.open(BytesIO(image_bytes)).convert("RGB").resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        return preprocess_input(img_array)

    def predict_image(processed_img):
        model = tf.keras.applications.MobileNetV2(weights="imagenet")
        predictions = model.predict(processed_img)
        decoded_preds = decode_predictions(predictions, top=3)[0]
        return decoded_preds

    processed_img = process_image(uploaded_file)
    predictions = predict_image(processed_img)

    return [
    {
        "classe": label,
        "score": f"{score * 100:.2f}%",
    }
    for (_, label, score) in predictions
    ]