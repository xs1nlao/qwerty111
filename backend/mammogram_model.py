import random
import time
from PIL import Image
import io

class MammogramAnalyzer:
    def __init__(self):
        print("🟢 Инициализация анализатора маммограмм (демо-режим)")
        self.available = True
        print("✅ Демо-режим активирован")
    
    def predict(self, image_bytes):
        """
        Анализ маммограммы - всегда возвращает случайный результат (демо)
        """
        print("🤖 Анализ в демо-режиме...")
        
        # Небольшая задержка для реалистичности
        time.sleep(1)
        
        # Пробуем прочитать изображение (но необязательно)
        try:
            image = Image.open(io.BytesIO(image_bytes))
            print(f"📸 Получено изображение: {image.size}")
        except:
            print("⚠️ Не удалось прочитать изображение, но анализ продолжается")
        
        # Генерируем случайный результат
        # 70% вероятность доброкачественного, 30% злокачественного
        is_malignant = random.random() > 0.7
        confidence = random.uniform(0.75, 0.98)
        
        # Выбираем случайные описания
        mass_types = ["нет", "с четкими контурами", "с нечеткими контурами"]
        calc_types = ["нет", "доброкачественные", "подозрительные"]
        
        result = {
            'success': True,
            'result': {
                'is_malignant': is_malignant,
                'label': 'Злокачественно' if is_malignant else 'Доброкачественно',
                'confidence': round(confidence, 2),
                'probability': round(confidence if is_malignant else 1 - confidence, 2),
                'details': {
                    'mass': random.choice(mass_types),
                    'calcifications': random.choice(calc_types),
                }
            },
            'model_info': {
                'accuracy': 85,
                'type': 'Демо-режим',
                'note': 'Тестовый режим (не для медицинского использования)'
            }
        }
        
        print(f"✅ Результат: {result['result']['label']} (уверенность: {confidence:.2f})")
        return result

# Глобальный экземпляр
analyzer = MammogramAnalyzer()

def get_mammogram_model():
    return analyzer