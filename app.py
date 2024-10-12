import streamlit as st
import numpy as np
import json
from src.generate import decode_vector_to_image
from PIL import Image
import torch
import torchvision.transforms as transforms
import onnxruntime as ort

# Инициализация ONNX-сессии
weights_path = "models/w600k_r50.onnx"
session = ort.InferenceSession(weights_path)

# Преобразования для изображений
transform = transforms.Compose([
    transforms.Resize((112, 112)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

st.title("VAE Image Processing")

# Страница для восстановления изображения из вектора
page = st.sidebar.selectbox("Выберите действие", ["Восстановить изображение", "Получить вектор из изображения"])

if page == "Восстановить изображение":
    st.header("Восстановление изображения из вектора")

    st.write("Загрузите файл с векторами (формат .npy или .json):")
    uploaded_file = st.file_uploader("Выберите файл", type=["npy", "json"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.npy'):
            vector = np.load(uploaded_file)
        elif uploaded_file.name.endswith('.json'):
            vector = np.array(json.load(uploaded_file))

        st.write("Полученный вектор:")
        st.write(vector)

        if st.button("Восстановить изображение"):
            image_array = decode_vector_to_image(vector)
            image_array = (image_array * 255).astype(np.uint8)  # Приведение к типу uint8
            image = Image.fromarray(image_array.reshape(112, 112, 3))  # Предполагаем, что изображение 112x112
            st.image(image, caption="Восстановленное изображение", use_column_width=True)

elif page == "Получить вектор из изображения":
    st.header("Получение вектора из изображения")

    st.write("Загрузите изображение:")
    uploaded_image = st.file_uploader("Выберите изображение", type=["jpg", "png"])

    if uploaded_image is not None:
        # Открытие и преобразование изображения
        img = Image.open(uploaded_image).convert('RGB')
        img_tensor = transform(img).unsqueeze(0).numpy()  # Добавление размерности batch

        # Извлечение вектора через ONNX-модель
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        vector = session.run([output_name], {input_name: img_tensor})[0]

        st.write("Извлечённый вектор:")
        st.write(vector)

        if st.button("Сохранить вектор"):
            vector_filename = st.text_input("Введите имя файла для сохранения (без расширения):", "")
            if vector_filename:
                np.save(f"{vector_filename}.npy", vector)
                st.success(f"Вектор сохранен как {vector_filename}.npy")

