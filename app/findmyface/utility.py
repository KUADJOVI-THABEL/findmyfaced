import boto3
import insightface
from PIL import Image
import io
import numpy as np
import cv2

# Globals
MODEL = None

def load_model(ctx_id=-1):
    """Charger le modèle ArcFace (singleton)."""
    global MODEL
    if MODEL is None:
        MODEL = insightface.app.FaceAnalysis()
        MODEL.prepare(ctx_id=ctx_id)
    return MODEL



def read_image_from_s3_pil(bucket_name, object_key):
    """Reads an image from S3 and returns a Pillow Image object."""
    s3 = boto3.resource("s3")
    s3_object = s3.Object(bucket_name, object_key)

    img_data = s3_object.get()["Body"].read()
    image = Image.open(io.BytesIO(img_data)).convert("RGB")  # force RGB

    return image


def get_face_embeddings(key, bucket, ctx_id=-1, test_mode=False):
    """
    Returns list of embeddings (numpy arrays) for all faces in the image.
    ctx_id: -1 CPU, 0 GPU
    """
    model = load_model(ctx_id=-1)  # CPU
   

    # 1) Load image
    if test_mode:
        img = cv2.imread(key)  # already numpy BGR
        if img is None:
            return []
    else:
        pil_img = read_image_from_s3_pil(bucket_name=bucket, object_key=key)
        if pil_img is None:
            return []

        # 2) PIL -> numpy (RGB)
        img = np.array(pil_img)

        # 3) RGB -> BGR (InsightFace expects BGR like OpenCV)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 4) Now img is numpy array with shape (H, W, 3)
    print("Image loaded, shape:", key, img.shape)

    faces = model.get(img)
    embeddings = [f.embedding for f in faces]

    return embeddings