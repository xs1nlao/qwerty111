from mammogram_model import get_mammogram_model

model = get_mammogram_model()

with open("test_mammogram.jpg", "rb") as f:
    image_bytes = f.read()

result = model.predict(image_bytes)
print(result)