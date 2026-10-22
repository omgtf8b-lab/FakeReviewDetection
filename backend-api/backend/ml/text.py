"""Shared preprocessing used by training, inference and explanations."""
import re


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+|<[^>]*>", " ", text)
    text = re.sub(r"[^a-zA-Z'\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_batch(texts):
    return [clean_text(text) for text in texts]
