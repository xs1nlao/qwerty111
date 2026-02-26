from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from ai_service import ai_service  
from patient_manager import patient_manager
import PyPDF2
from docx import Document
import io
from scoring import scorer
from metrics_collector import metrics_collector
from mammogram_model import get_mammogram_model
from knowledge_base_loader import kb_loader
from typing import Dict, List, Any, Optional


load_dotenv()


import PyPDF2
from docx import Document
import io

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

print("🟢 Инициализация модели маммограмм...")
try:
    # Импортируем из нашего файла
    from mammogram_model import get_mammogram_model
    mammogram_model = get_mammogram_model()
    print("✅ Модель маммограмм загружена!")
except Exception as e:
    print(f"⚠️ Ошибка загрузки модели маммограмм: {e}")
    # Создаем простую заглушку прямо здесь
    class SimpleMammogram:
        def predict(self, image_bytes):
            import random
            return {
                'success': True,
                'result': {
                    'is_malignant': random.random() > 0.7,
                    'label': 'Результат',
                    'confidence': 0.85,
                    'probability': 0.85
                },
                'model_info': {
                    'type': 'Заглушка',
                    'note': 'Демо-режим'
                }
            }
    mammogram_model = SimpleMammogram()
    print("✅ Используется встроенная заглушка")


SYSTEM_PROMPTS = {
    'analysis': """Ты - опытный онколог. Проанализируй историю болезни.

ВАЖНО: Не рассчитывай compliance_score самостоятельно! Просто опиши ситуацию.

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{
    "doctor_version": {
        "summary": "краткое заключение по истории",
        "diagnosis": {
            "extracted": "диагноз из истории",
            "stage": "стадия",
            "notes": "замечания по диагнозу"
        },
        "findings": [
            {
                "category": "хирургия/химиотерапия/лучевая/таргетная",
                "prescribed": "что назначено (конкретные препараты)",
                "status": "info",
                "comment": "комментарий по назначению",
                "sources": ["NCCN", "ESMO", "Минздрав РФ"]
            }
        ]
    },
    "patient_version": {
        "summary": "понятное заключение для пациента",
        "status": "📋",
        "key_points": ["список понятных пунктов"],
        "questions_for_doctor": ["вопросы к врачу"]
    }
}

ПРАВИЛА:
1. Отвечай ТОЛЬКО на русском языке
2. НЕ ставь compliance_score - это рассчитает система
3. Не используй ФИО пациентов
4. Для пациента - простой язык, без сложных терминов"""
}

def anonymize_text(text):
    """
    Заменяет потенциальные персональные данные на заглушки
    """
    if not text:
        return text
    
    patterns = [
        (r'\b[А-Я][а-я]+ [А-Я][а-я]+ [А-Я][а-я]+\b', '[ФИО]'),
        (r'\b[А-Я][а-я]+ [А-Я][а-я]+\b', '[ФИО]'),
        (r'\b[А-Я][а-я]+ [А-Я]\.?[А-Я]\.?\b', '[ФИО]'),
        (r'\b\d{2}\.\d{2}\.\d{4}\b', '[ДАТА]'),
        (r'\b\d{2}/\d{2}/\d{4}\b', '[ДАТА]'),
        (r'\b\d{4} \d{6}\b', '[ПАСПОРТ]'),
        (r'\b\d{4}-\d{6}\b', '[ПАСПОРТ]'),
        (r'\b\d{3}-\d{3}-\d{3} \d{2}\b', '[СНИЛС]'),
        (r'\b\d{11}\b', '[СНИЛС]'),
        (r'\+7[\d\-\(\) ]{10,}', '[ТЕЛЕФОН]'),
        (r'8[\d\-\(\) ]{10,}', '[ТЕЛЕФОН]'),
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
        (r'(?:ул|пр|проспект|пер|переулок|бульвар|пл|площадь)\.?\s+[А-Яа-я]+', '[АДРЕС]'),
        (r'г\.?\s*[А-Я][а-я]+', '[ГОРОД]'),
    ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    
    return text


def extract_text_from_pdf(file_bytes):
    """Извлекает текст из PDF"""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Ошибка чтения PDF: {e}")
    return text


def extract_text_from_docx(file_bytes):
    """Извлекает текст из DOCX"""
    text = ""
    try:
        doc = Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    except Exception as e:
        print(f"Ошибка чтения DOCX: {e}")
    return text


def extract_text_from_file(file_bytes, filename):
    """Унифицированная функция для извлечения текста из файла"""
    try:
        if filename.endswith('.txt'):
            return file_bytes.decode('utf-8', errors='ignore')
        elif filename.endswith('.pdf'):
            return extract_text_from_pdf(file_bytes)
        elif filename.endswith(('.docx', '.doc')):
            return extract_text_from_docx(file_bytes)
        else:
            return ""
    except Exception as e:
        print(f"❌ Ошибка извлечения текста из {filename}: {e}")
        return f"[Ошибка чтения файла: {filename}]"


def safe_parse_ai_response(content):
    """Безопасный парсинг JSON от DeepSeek с восстановлением"""
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    if not content:
        print("❌ Пустой ответ от AI")
        return create_fallback_response("Пустой ответ от AI"), False
    
    print(f"📄 Попытка парсинга JSON, длина: {len(content)} символов")
    
    timestamp = int(time.time())
    debug_file = os.path.join(logs_dir, f"debug_response_{timestamp}.json")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Ответ сохранен в {debug_file}")
    
    try:
        return json.loads(content), True
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
    
    cleaned = content.strip()
    
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    json_match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str), True
        except:
            pass
    
    print("❌ Все попытки восстановления JSON failed")
    return create_fallback_response("Ошибка парсинга ответа AI"), False


def create_fallback_response(error_message="Ошибка обработки"):
    """Создает корректный fallback ответ"""
    return {
        "doctor_version": {
            "summary": f"Ошибка обработки ответа AI: {error_message}",
            "compliance_score": 50,
            "diagnosis": {
                "extracted": "Ошибка парсинга",
                "stage": "Не указана",
                "notes": "AI вернул некорректный JSON"
            },
            "findings": [
                {
                    "category": "Общий анализ",
                    "prescribed": "Данные не получены",
                    "status": "warning",
                    "comment": "Не удалось распарсить ответ AI. Попробуйте еще раз.",
                    "sources": ["NCCN Guidelines", "ESMO Guidelines"]
                }
            ],
            "references": ["Клинические рекомендации Минздрава РФ"]
        },
        "patient_version": {
            "summary": "Произошла ошибка при анализе",
            "status": "⚠️",
            "key_points": [
                "Не удалось обработать ответ AI",
                "Попробуйте повторить запрос позже"
            ],
            "questions_for_doctor": ["Что делать, если анализ не работает?"]
        }
    }


def extract_treatments_from_answer(answer: str) -> List[str]:
    """
    Извлекает препараты из ответа пользователя на вопрос о планируемом лечении
    """
    treatments = []
    
    treatment_mapping = {
        'Трастузумаб-эмтансин (T-DM1)': ['трастузумаб-эмтансин', 'трастузумаб', 'т-дм1'],
        'Трастузумаб дерукстекан': ['трастузумаб дерукстекан', 'энхерту'],
        'Комбинация трастузумаба с химиотерапией': ['трастузумаб', 'паклитаксел', 'доцетаксел'],
        'Иммунотерапия (ингибиторы PD-1/PD-L1)': ['пембролизумаб', 'ниволумаб', 'атезолизумаб'],
        'Другая таргетная терапия': ['тукатиниб', 'лапатиниб', 'нератиниб'],
        'Химиотерапия без таргетных препаратов': ['паклитаксел', 'доцетаксел', 'гемцитабин'],
        'Наблюдение (без лечения)': []
    }
    
    if answer in treatment_mapping:
        treatments = treatment_mapping[answer]
    
    return treatments


print("🟢 Инициализация модели маммограмм...")
try:
    try:
        from mammogram_winner import get_mammogram_model
        mammogram_model = get_mammogram_model()
        print("✅ Модель маммограмм загружена!")
    except ImportError:
        print("⚠️ Модуль mammogram_winner не найден, используется заглушка")
        mammogram_model = None
except Exception as e:
    print(f"⚠️ Ошибка загрузки модели маммограмм: {e}")
    mammogram_model = None

print("✅ AI Service уже инициализирован при импорте")


@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'DeepSeek работает!'})


@app.route('/api/mammogram/analyze', methods=['POST', 'OPTIONS'])
def analyze_mammogram():
    # Обработка OPTIONS запросов (CORS)
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    try:
        print("\n🔴🔴🔴 МАММОГРАММА: Получен запрос")
        
        # Проверяем наличие файла
        if 'file' not in request.files:
            print("❌ Нет файла в запросе")
            return jsonify({'error': 'Нет файла', 'success': False}), 400
        
        file = request.files['file']
        print(f"📎 Получен файл: {file.filename}")
        
        # Читаем файл
        image_bytes = file.read()
        
        # Получаем модель (глобальная переменная)
        global mammogram_model
        
        # Если модели нет, создаем заглушку
        if mammogram_model is None:
            print("⚠️ Модель не загружена, создаем заглушку")
            class DummyMammogram:
                def predict(self, img_bytes):
                    import random
                    import time
                    time.sleep(0.5)
                    is_malignant = random.random() > 0.7
                    return {
                        'success': True,
                        'result': {
                            'is_malignant': is_malignant,
                            'label': 'Злокачественно' if is_malignant else 'Доброкачественно',
                            'confidence': 0.85,
                            'probability': 0.85 if is_malignant else 0.15
                        },
                    }
            mammogram_model = DummyMammogram()
        
        # Вызываем модель
        print("🤖 Вызываем модель...")
        result = mammogram_model.predict(image_bytes)
        print(f"✅ Результат получен")
        
        # Добавляем patient_id если есть
        patient_id = request.form.get('patient_id')
        if patient_id:
            result['patient_id'] = patient_id
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Ошибка в analyze_mammogram: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/patient/<patient_id>/history/<entry_id>', methods=['DELETE', 'OPTIONS'])
def delete_history_entry(patient_id, entry_id):
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        return response, 200
    
    try:
        print(f"\n🗑️ ЗАПРОС НА УДАЛЕНИЕ: Patient {patient_id}, Entry {entry_id}")
        
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Пациент не найден'}), 404
        
        original_length = len(patient.get('history', []))
        patient['history'] = [h for h in patient.get('history', []) if h.get('id') != entry_id]
        new_length = len(patient.get('history', []))
        
        if original_length == new_length:
            return jsonify({'error': 'Запись не найдена'}), 404
        
        patient_manager._save_patients()
        
        return jsonify({
            'success': True,
            'message': 'Запись удалена',
            'deleted_id': entry_id,
            'new_count': new_length
        })
        
    except Exception as e:
        print(f"❌ Ошибка при удалении записи: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/patient/<patient_id>/history/clear', methods=['POST', 'OPTIONS'])
def clear_patient_history(patient_id):
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    try:
        print(f"🧹 Очистка всей истории пациента {patient_id}")
        
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Пациент не найден'}), 404
        
        old_count = len(patient.get('history', []))
        patient['history'] = []
        patient['timeline'] = []
        
        patient_manager._save_patients()
        
        return jsonify({
            'success': True,
            'message': 'История очищена',
            'deleted_count': old_count
        })
        
    except Exception as e:
        print(f"❌ Ошибка при очистке истории: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics', methods=['GET', 'OPTIONS'])
def get_metrics():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response, 200
    
    try:
        print("📊 Запрос метрик")
        metrics = metrics_collector.get_metrics_report()
        
        if not metrics:
            metrics = {
                'period': {
                    'start': datetime.now().strftime('%Y-%m-%d'),
                    'end': datetime.now().strftime('%Y-%m-%d'),
                    'days': 0
                },
                'volume': {'total_analyses': 0, 'analyses_per_day': 0},
                'performance': {
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'response_time_distribution': {'<1s': 0, '1-2s': 0, '2-3s': 0, '3-4s': 0, '>4s': 0}
                },
                'cache': {'hits': 0, 'hit_rate': 0},
                'quality': {
                    'avg_compliance_score': 0,
                    'score_distribution': {'high': 0, 'medium': 0, 'low': 0}
                },
                'cancer_types': {},
                'errors': {'total': 0, 'error_rate': 0},
                'mammogram': {
                    'total': 0, 'malignant': 0, 'benign': 0,
                    'malignant_rate': 0, 'avg_confidence': 0
                }
            }
        
        return jsonify({'success': True, 'metrics': metrics})
        
    except Exception as e:
        print(f"❌ Ошибка получения метрик: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/patients', methods=['GET'])
def get_patients():
    patients_list = patient_manager.get_all_patients()
    return jsonify({"patients": patients_list})


@app.route('/api/patients/create', methods=['POST'])
def create_patient():
    try:
        data = request.json
        initials = data.get('initials', '')
        age = data.get('age', 0)
        gender = data.get('gender', '')
        
        patient_id = patient_manager.create_patient(initials, age, gender)
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'patient': patient_manager.get_patient(patient_id)
        })
    except Exception as e:
        print(f"Create patient error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/search', methods=['GET'])
def search_patients():
    query = request.args.get('q', '')
    results = patient_manager.search_patients(query)
    return jsonify({'results': results})


@app.route('/api/patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = patient_manager.get_patient(patient_id)
    if not patient:
        return jsonify({'error': 'Пациент не найден'}), 404
    
    patient_info = {
        "id": patient["id"],
        "initials": patient.get("initials", ""),
        "age": patient.get("age", 0),
        "gender": patient.get("gender", ""),
        "diagnosis": patient.get("diagnosis", ""),
        "last_visit": patient.get("last_visit", ""),
        "created_at": patient.get("created_at", ""),
        "history_count": len(patient.get("history", []))
    }
    
    return jsonify({"patient": patient_info})


@app.route('/api/patient/<patient_id>/history', methods=['GET'])
def get_patient_history(patient_id):
    patient = patient_manager.get_patient(patient_id)
    
    if not patient:
        return jsonify({"history": []})
    
    history = patient.get("history", [])
    return jsonify({"history": history})


@app.route('/api/patient/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Пациент не найден'}), 404
        
        if patient_id in patient_manager.patients:
            del patient_manager.patients[patient_id]
            patient_manager._save_patients()
            return jsonify({'success': True, 'message': 'Пациент удален'})
        else:
            return jsonify({'error': 'Пациент не найден'}), 404
            
    except Exception as e:
        print(f"❌ Ошибка при удалении пациента: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-analysis', methods=['POST', 'OPTIONS'])
def update_analysis():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    start_time = time.time()
    
    try:
        data = request.json
        patient_id = data.get('patientId')
        answers = data.get('answers', {})
        original_history = data.get('originalHistory', '')
        cancer_type = data.get('cancerType', '')
        
        print(f"\n🔄 ОБНОВЛЕНИЕ АНАЛИЗА для пациента {patient_id}")
        print(f"📝 Получены ответы: {answers}")
        
        impacts_score = False
        new_treatment = None
        
        score_impacting_keys = ['planned_treatment', 'her2_therapy_type', 't790m_status', 'ihc_markers', 'pd_l1_cps']
        
        for key, value in answers.items():
            if key in score_impacting_keys:
                impacts_score = True
                if key == 'planned_treatment' or key == 'her2_therapy_type':
                    new_treatment = value
                print(f"⚠️ Найден вопрос, влияющий на score: {key} = {value}")
        
        patient = patient_manager.get_patient(patient_id)
        old_analysis = None
        old_score_result = None
        old_treatment_lines = None 
        
        if patient and patient.get('history') and len(patient['history']) > 0:
            old_analysis = patient['history'][-1].get('full_result', {})
            old_score_result = old_analysis.get('doctor_version', {}).get('compliance_details')
            
            old_treatment_lines = old_analysis.get('doctor_version', {}).get('treatment_lines')
            
            if isinstance(old_treatment_lines, list):
                print(f"⚠️ Обнаружен список вместо словаря, преобразую...")
                old_treatment_lines = {"lines": old_treatment_lines, "planned": None}
            
            print(f"📋 Найден предыдущий анализ: score={old_score_result.get('score') if old_score_result else 'N/A'}")
        
        enhanced_history = anonymize_text(original_history) + "\n\nДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:\n"
        for key, value in answers.items():
            enhanced_history += f"- {key}: {value}\n"
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS['analysis']},
                {"role": "user", "content": enhanced_history}
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return jsonify({'error': f'Ошибка DeepSeek: {response.status_code}'}), 500
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        new_ai_response, parse_success = safe_parse_ai_response(content)
        
        new_score_result = None
        
        if impacts_score and new_treatment:
            print(f"🔄 Пересчитываем score с учетом нового лечения: {new_treatment}")
            
            prescribed_treatments = extract_treatments_from_answer(new_treatment)
            
            if not prescribed_treatments:
                prescribed_treatments = ai_service.extract_treatments_with_ai(enhanced_history)
            
            biomarkers = ai_service.extract_biomarkers(enhanced_history)
            
            temp_lines = {
                'lines': [{'line': 1, 'treatments': prescribed_treatments, 'response': 'планируется'}]
            }
            
            new_score_result = scorer.calculate_score_from_protocols(
                cancer_type=cancer_type,
                treatment_lines=temp_lines,
                biomarkers=biomarkers
            )
            
            print(f"✅ Score пересчитан: {new_score_result['score']}%")
        
        elif impacts_score:
            print("⚠️ Есть вопросы, влияющие на score, но новое лечение не определено")
            new_score_result = old_score_result
        else:
            print("ℹ️ Вопросы не влияют на score, сохраняем существующий расчет")
            new_score_result = old_score_result
        
        enhanced_response = ai_service.enhance_response_with_guidelines(
            patient_history=enhanced_history,
            ai_response=new_ai_response,
            cancer_type=cancer_type,
            is_update=True,
            precomputed_score=new_score_result,
            treatment_lines=old_treatment_lines  
        )
        
        if patient_id:
            patient_manager.add_history_entry(patient_id, enhanced_history, enhanced_response)
        
        try:
            compliance_score = enhanced_response.get('doctor_version', {}).get('compliance_score', 0)
            response_time = time.time() - start_time
            source = enhanced_response.get('doctor_version', {}).get('compliance_details', {}).get('source', 'unknown')
            
            metrics_collector.record_analysis(
                cancer_type=cancer_type,
                compliance_score=compliance_score,
                response_time=response_time,
                from_cache=False,
                source=source
            )
        except Exception as e:
            print(f"⚠️ Ошибка записи метрик: {e}")
        
        return jsonify({
            'success': True,
            'result': enhanced_response,
            'score_updated': impacts_score
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Сервер AI не отвечает'}), 504
    except Exception as e:
        print(f"❌ Ошибка в update_analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-treatment', methods=['POST', 'OPTIONS'])
def check_treatment():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    start_time = time.time()
    
    try:
        print("\n" + "="*60)
        print("🔥 ПОЛУЧЕН ЗАПРОС НА /api/check-treatment")
        print("="*60)
        
        print("📥 ШАГ 1: Получение данных запроса")
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        history = data.get('history', '')
        patient_id = data.get('patient_id', None)
        
        if not history or history.strip() == "":
            return jsonify({'error': 'Нет истории болезни'}), 400
        
        print(f"📝 История получена, длина: {len(history)} символов")
        print(f"🆔 Patient ID: {patient_id}")
        
        print("🔄 ШАГ 2: Анонимизация данных")
        history = anonymize_text(history)
        
        print("👤 ШАГ 3: Работа с пациентом")
        if not patient_id:
            patient_id = patient_manager.create_patient()
            print(f"✅ Создан новый пациент: {patient_id}")
        else:
            patient = patient_manager.get_patient(patient_id)
            if not patient:
                patient_id = patient_manager.create_patient_with_id(patient_id)
                print(f"✅ Создан пациент с ID: {patient_id}")
            else:
                print(f"✅ Найден пациент: {patient_id}")
        
        print("🤖 ШАГ 4: Запрос к DeepSeek API")
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS['analysis']},
                {"role": "user", "content": history}
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        print("📤 Отправка запроса к DeepSeek...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Ошибка DeepSeek: {response.status_code}")
            return jsonify({'error': f'Ошибка DeepSeek: {response.status_code}'}), 500
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"📄 Получен ответ, длина: {len(content)} символов")
        
        print("🔧 ШАГ 5: Парсинг JSON ответа")
        ai_response, parse_success = safe_parse_ai_response(content)
        print(f"✅ Парсинг успешен: {parse_success}")
        
        print("🔍 ШАГ 6: Определение типа рака")
        cancer_type = ai_service.detect_cancer_type(history)
        print(f"📊 Тип рака: {cancer_type}")
        
        print("🧬 ШАГ 7: Извлечение биомаркеров")
        biomarkers = ai_service.extract_biomarkers(history)
        print(f"📊 Биомаркеры: {biomarkers}")
        
        print("📋 ШАГ 8: Извлечение линий терапии")
        treatment_lines = ai_service.extract_treatment_lines(history)
        print(f"✅ Найдено линий: {len(treatment_lines.get('lines', []))}")
        
        print("📊 ШАГ 9: Расчет compliance score")
        score_result = scorer.calculate_score_from_protocols(
            cancer_type=cancer_type,
            treatment_lines=treatment_lines,
            biomarkers=biomarkers
        )
        print(f"✅ Score: {score_result['score']}%")
        print(f"📌 Источник: {score_result.get('source', 'unknown')}")
        
        print("🔄 ШАГ 10: Упрощение ответа для пациента")
        try:

            doctor_version = ai_response.get('doctor_version', {})
            findings = doctor_version.get('findings', [])

            simple_findings = []
            for f in findings:
                status = f.get('status', '')
                treatment = f.get('prescribed', f.get('treatment', ''))
                if status == 'correct':
                    simple_findings.append(f"✅ {treatment} - правильно")
                elif status == 'warning':
                    simple_findings.append(f"⚠️ {treatment} - нужен контроль")
                elif status == 'critical':
                    simple_findings.append(f"❌ {treatment} - ошибка")

            current_patient = ai_response.get('patient_version', {})
            
            simplify_prompt = f"""Ты - онколог, но объясняешь сложные вещи простым языком для пациента.

Диагноз: {cancer_type}
Общий результат: {score_result['score']}% соответствия стандартам

Что важно знать:
{chr(10).join(simple_findings[:5]) if simple_findings else 'Лечение в целом соответствует стандартам'}

ПЕРЕПИШИ ЭТО ОЧЕНЬ ПРОСТО:

1. summary: Напиши 1-2 предложения самым простым языком.
2. key_points: Список из 3-5 самых важных моментов.
3. questions_for_doctor: Список простых вопросов.

Верни ТОЛЬКО JSON.
"""
            
            simplify_payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты - врач, который объясняет сложные вещи простым языком. Отвечаешь только JSON."},
                    {"role": "user", "content": simplify_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            print("📤 Запрос на упрощение...")
            simplify_response = requests.post(
                DEEPSEEK_API_URL, 
                headers=headers, 
                json=simplify_payload, 
                timeout=30
            )
            
            if simplify_response.status_code == 200:
                simplify_result = simplify_response.json()
                simplified = json.loads(simplify_result['choices'][0]['message']['content'])
                
                if 'patient_version' not in ai_response:
                    ai_response['patient_version'] = {}
                
                ai_response['patient_version']['summary'] = simplified.get('summary', current_patient.get('summary', 'Анализ завершен'))
                ai_response['patient_version']['key_points'] = simplified.get('key_points', current_patient.get('key_points', []))
                ai_response['patient_version']['questions_for_doctor'] = simplified.get('questions_for_doctor', current_patient.get('questions_for_doctor', []))
                ai_response['patient_version']['status'] = '📋'
                
                print("✅ Ответ упрощен для пациента")
            else:
                print(f"⚠️ Ошибка упрощения: {simplify_response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Ошибка при упрощении: {e}")
            import traceback
            traceback.print_exc()
            if 'patient_version' not in ai_response:
                ai_response['patient_version'] = {
                    'summary': 'Анализ завершен',
                    'status': '📋',
                    'key_points': ['Лечение проверено'],
                    'questions_for_doctor': ['Задайте вопросы врачу']
                }
        
        print("📦 ШАГ 11: Обогащение ответа из базы знаний")
        enhanced_response = ai_service.enhance_response_with_guidelines(
            patient_history=history,
            ai_response=ai_response,
            cancer_type=cancer_type,
            is_update=False,
            precomputed_score=score_result,
            treatment_lines=treatment_lines
        )
        

        print("📊 ШАГ 12: Запись метрик")
        try:
            response_time = time.time() - start_time
            metrics_collector.record_analysis(
                cancer_type=cancer_type,
                compliance_score=score_result['score'],
                response_time=response_time,
                from_cache=False,
                source=score_result.get('source', 'unknown')
            )
        except Exception as e:
            print(f"⚠️ Ошибка записи метрик: {e}")
        

        print("💾 ШАГ 13: Сохранение в историю пациента")
        patient_manager.add_history_entry(patient_id, history, enhanced_response)

        print("📨 ШАГ 14: Формирование ответа клиенту")
        return jsonify({
            'success': True,
            'result': enhanced_response,
            'patient_id': patient_id,
            'analysis_details': {
                'cancer_type': cancer_type,
                'lines_found': len(treatment_lines.get('lines', [])),
                'score': score_result['score'],
                'source': score_result.get('source', 'unknown'),
                'protocols_available': len(scorer.protocols_db.get(cancer_type, [])),
                'analysis_time': round(time.time() - start_time, 2)
            }
        })
        
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
        return jsonify({'error': 'Сервер AI не отвечает. Попробуйте позже.'}), 504
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return jsonify({'error': 'Ошибка соединения с сервером AI'}), 503
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        

        error_msg = str(e)
        if 'detect_cancer_type' in error_msg:
            step = 'определение типа рака'
        elif 'extract_biomarkers' in error_msg:
            step = 'извлечение биомаркеров'
        elif 'extract_treatment_lines' in error_msg:
            step = 'извлечение линий терапии'
        elif 'calculate_score_from_protocols' in error_msg:
            step = 'расчет score'
        elif 'enhance_response_with_guidelines' in error_msg:
            step = 'обогащение ответа'
        else:
            step = 'неизвестный'
        
        fallback_response = {
            'success': False,
            'error': f'Ошибка на шаге: {step}',
            'details': str(e),
            'fallback': {
                'message': 'Произошла ошибка при анализе. Пожалуйста, попробуйте еще раз.',
                'cancer_type': 'unknown',
                'compliance_score': 50
            }
        }
        return jsonify(fallback_response), 500


@app.route('/api/check-treatment-with-files', methods=['POST', 'OPTIONS'])
def check_treatment_with_files():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    start_time = time.time()
    
    try:
        print("\n" + "="*50)
        print("🔥 ПОЛУЧЕН ЗАПРОС С ФАЙЛАМИ")
        print("="*50)
        
        history = request.form.get('history', '')
        patient_id = request.form.get('patient_id', None)
        files = request.files.getlist('files')
        
        if not history and len(files) == 0:
            return jsonify({'error': 'Нет данных для анализа'}), 400
        
        extracted_text = history
        if files:
            extracted_text += "\n\n--- ИЗВЛЕЧЕННЫЙ ТЕКСТ ИЗ ФАЙЛОВ ---\n"
        
        for file in files:
            filename = file.filename
            file_bytes = file.read()
            text = extract_text_from_file(file_bytes, filename)
            if text:
                extracted_text += f"\n[{filename}]\n{text}\n"
        
        extracted_text = anonymize_text(extracted_text)
        
        if patient_id:
            patient = patient_manager.get_patient(patient_id)
            if not patient:
                patient_id = patient_manager.create_patient_with_id(patient_id)
        else:
            patient_id = patient_manager.create_patient()
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS['analysis']},
                {"role": "user", "content": extracted_text}
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return jsonify({'error': f'Ошибка DeepSeek: {response.status_code}'}), 500
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        ai_response, parse_success = safe_parse_ai_response(content)

        cancer_type = ai_service.detect_cancer_type(extracted_text)
        biomarkers = ai_service.extract_biomarkers(extracted_text)
        treatment_lines = ai_service.extract_treatment_lines(extracted_text)
        
        score_result = scorer.calculate_score_from_protocols(
            cancer_type=cancer_type,
            treatment_lines=treatment_lines,
            biomarkers=biomarkers
        )
        
        enhanced_response = ai_service.enhance_response_with_guidelines(
            patient_history=extracted_text,
            ai_response=ai_response,
            cancer_type=cancer_type,
            is_update=False,
            precomputed_score=score_result,
            treatment_lines=treatment_lines
        )
        
        try:
            response_time = time.time() - start_time
            metrics_collector.record_analysis(
                cancer_type=cancer_type,
                compliance_score=score_result['score'],
                response_time=response_time,
                from_cache=False,
                source=score_result.get('source', 'unknown')
            )
        except Exception as e:
            print(f"⚠️ Ошибка записи метрик: {e}")
        
        success = patient_manager.add_history_entry(patient_id, extracted_text, enhanced_response)
        
        return jsonify({
            'success': True,
            'result': enhanced_response,
            'patient_id': patient_id
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-history/<patient_id>', methods=['POST'])
def clear_history(patient_id):
    patient = patient_manager.get_patient(patient_id)
    if patient:
        patient["history"] = []
        patient["timeline"] = []
        patient_manager._save_patients()
        return jsonify({"success": True, "message": "История очищена"})
    return jsonify({"error": "Пациент не найден"}), 404


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 ЗАПУСК ONCOLOGY AI ASSISTANT")
    print("="*50)
    print(f"🔑 API Key: {DEEPSEEK_API_KEY[:10]}..." if DEEPSEEK_API_KEY else "❌ API Key не найден!")
    print("🤖 AI Service инициализирован")
    print(f"📁 База пациентов: patients_db.json")
    print("\n📋 Доступные эндпоинты:")
    print("   - /api/check-treatment (JSON)")
    print("   - /api/check-treatment-with-files (FormData + файлы)")
    print("   - /api/update-analysis")
    print("   - /api/patients")
    print("   - /api/mammogram/analyze")
    print("="*50 + "\n")
    
    os.makedirs("logs", exist_ok=True)
    app.run(port=5000, debug=True)