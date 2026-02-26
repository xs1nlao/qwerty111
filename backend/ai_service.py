
import os
import json
import re
import requests
import uuid
import time
from typing import Dict, List, Any, Optional
from cancer_links import get_cancer_link
from nccn_links import get_nccn_link
from esmo_links import get_esmo_link
from scoring import scorer
from knowledge_base_loader import kb_loader
from treatment_extractor import TreatmentLineExtractor

class AIService:
    def __init__(self):
        print("🟢 ИНИЦИАЛИЗАЦИЯ AI SERVICE")
        
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        
        self.guidelines_data = {}
        
        self.line_extractor = TreatmentLineExtractor(self.deepseek_api_key)

        self.knowledge_base = kb_loader
        if self.knowledge_base and hasattr(self.knowledge_base, 'guidelines'):
            print(f"✅ База знаний загружена: {len(self.knowledge_base.guidelines)} рекомендаций")
        else:
            print("⚠️ База знаний не загружена или пуста")
        
        print("✅ AI Service инициализирован")
    
    def detect_cancer_type(self, text: str) -> str:
        """
        Использует AI для определения типа рака из текста
        """
        print("\n🔍 AI ОПРЕДЕЛЯЕТ ТИП РАКА")
        
        try:
            prompt = f"""Проанализируй историю болезни и определи ОСНОВНОЙ тип рака.
    Верни ТОЛЬКО одно слово из списка допустимых значений.

    История болезни:
    {text[:2000]}

    Допустимые значения:
    - 'cancer_unknown_primary' - если это CUP (неизвестный первичный очаг)
    - 'lung' - рак легкого
    - 'breast' - рак молочной железы
    - 'prostate' - рак предстательной железы
    - 'colon' - рак толстой кишки
    - 'rectal' - рак прямой кишки
    - 'stomach' - рак желудка
    - 'pancreatic' - рак поджелудочной железы
    - 'esophageal' - рак пищевода
    - 'liver' - рак печени
    - 'kidney' - рак почки
    - 'bladder' - рак мочевого пузыря
    - 'ovarian' - рак яичников
    - 'cervical' - рак шейки матки
    - 'uterine' - рак матки
    - 'melanoma' - меланома
    - 'thyroid' - рак щитовидной железы
    - 'general' - если не удалось определить или другое

    Верни ТОЛЬКО одно слово из списка выше, без пояснений.
    """

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты - онколог. Определяешь тип рака по истории болезни. Отвечаешь только одним словом."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
            
            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                cancer_type = result['choices'][0]['message']['content'].strip().lower()
                
                valid_types = ['cancer_unknown_primary', 'lung', 'breast', 'prostate', 'colon', 
                            'rectal', 'stomach', 'pancreatic', 'esophageal', 'liver', 'kidney', 
                            'bladder', 'ovarian', 'cervical', 'uterine', 'melanoma', 'thyroid', 'general']
                
                if cancer_type in valid_types:
                    print(f"✅ AI определил тип рака: {cancer_type}")
                    return cancer_type
                else:
                    print(f"⚠️ AI вернул недопустимое значение: {cancer_type}, используем fallback")
        
        except Exception as e:
            print(f"❌ Ошибка при вызове AI для определения типа рака: {e}")
        
        return self._fallback_detect_cancer_type(text)

    def _fallback_detect_cancer_type(self, text: str) -> str:
        """
        Запасной метод определения типа рака через ключевые слова
        """
        text_lower = text.lower()
        
        cup_keywords = ['невыявленного первичного', 'cup', 'неизвестного первичного', 'онпл', 'primary unknown']
        for keyword in cup_keywords:
            if keyword in text_lower:
                return 'cancer_unknown_primary'
        
        cancer_keywords = {
            'lung': ['рак легкого', 'рак легких', 'аденокарцинома легкого'],
            'breast': ['рак молочной железы', 'рак груди', 'рмж'],
            'prostate': ['рак предстательной железы', 'рак простаты'],
            'colon': ['рак ободочной кишки', 'рак толстой кишки'],
            'rectal': ['рак прямой кишки'],
            'stomach': ['рак желудка'],
            'pancreatic': ['рак поджелудочной железы'],
            'melanoma': ['меланома'],
            'thyroid': ['рак щитовидной железы']
        }
        
        for cancer_type, keywords in cancer_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return cancer_type
        
        return 'general'
    
    def extract_treatment_lines(self, history: str) -> Dict[str, Any]:
        """
        Извлекает линии терапии с помощью AI
        Всегда возвращает словарь с ключами 'lines' и 'planned'
        """

        if not hasattr(self, 'line_extractor'):
            self.line_extractor = TreatmentLineExtractor(self.deepseek_api_key)

        result = self.line_extractor.extract_lines(history)

        if not isinstance(result, dict):
            print("⚠️ AI вернул не словарь, использую fallback")
            result = self.line_extractor.extract_lines_fallback(history)
        
        if 'lines' not in result:
            result['lines'] = []
        if 'planned' not in result:
            result['planned'] = None

        if not result.get('lines'):
            print("⚠️ AI не извлек линии, использую fallback")
            fallback_result = self.line_extractor.extract_lines_fallback(history)
            if fallback_result.get('lines'):
                result = fallback_result
        
        return result
    
    def ask_about_treatment(self, cancer_type: str, treatment: str, biomarkers: Dict[str, bool]) -> Dict:
        """
        Спрашивает AI, подходит ли препарат - СТРОГАЯ ВЕРСИЯ
        """
        try:
            prompt = f"""Ты - строгий онколог, следующий клиническим рекомендациям. Оцени препарат.

    Тип рака: {cancer_type}
    Препарат: {treatment}
    Биомаркеры: {json.dumps(biomarkers, ensure_ascii=False, indent=2)}

    КРИТЕРИИ ОЦЕНКИ (будь строг!):
    1. Соответствует ли препарат стандартам лечения для этого типа рака?
    2. Учитывает ли он биомаркеры? (HER2, EGFR, PD-L1 и т.д.)
    3. Есть ли противопоказания или неэффективность?

    ПРИМЕРЫ НЕДОПУСТИМЫХ НАЗНАЧЕНИЙ:
    - Трастузумаб при HER2-негативном раке желудка → противопоказан (0 баллов)
    - Тамоксифен при раке желудка → не применяется (0 баллов)
    - Гемцитабин в 1 линии рака желудка → нестандартно (низкий балл)

    Ответь строго в формате JSON:
    {{
        "is_appropriate": true/false,
        "is_contraindicated": true/false,
        "explanation": "краткое объяснение",
        "confidence": 0.0-1.0,
        "score_recommendation": 0-25  # Рекомендуемый балл (0-25)
    }}
"""

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты - онколог. Отвечаешь только JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    return json.loads(content)
                except:
                    return {
                        "is_appropriate": True,
                        "is_contraindicated": False,
                        "explanation": "AI не смог оценить",
                        "confidence": 0.5
                    }
        except Exception as e:
            print(f"❌ Ошибка в ask_about_treatment: {e}")
        
        return {
            "is_appropriate": True,
            "is_contraindicated": False,
            "explanation": "Оценка по умолчанию",
            "confidence": 0.5
        }
    
    def get_protocol_info(self, cancer_type: str, prescribed_regimen: str, biomarkers: Dict = None) -> Optional[Dict]:
        """
        Сравнивает назначенный режим с рекомендованными из базы знаний.
        """
        if not self.knowledge_base:
            return None

        protocols = self.knowledge_base.get_protocols(cancer_type)
        
        if not protocols:
            return None
        
        regimen_found = False
        recommended_regimens = []
        matching_protocols = []
        
        for protocol in protocols:
            meds = protocol.get('medications', [])
            recommended_regimens.extend(meds)
            
            protocol_name = protocol.get('protocol_name', '').lower()
            if prescribed_regimen and prescribed_regimen.lower() in protocol_name:
                regimen_found = True
                matching_protocols.append(protocol)
                continue
            
            for med in meds:
                if prescribed_regimen and med.lower() in prescribed_regimen.lower():
                    regimen_found = True
                    matching_protocols.append(protocol)
                    break
        
        return {
            "found": regimen_found,
            "recommended_regimens": list(set(recommended_regimens))[:10],
            "protocol_count": len(protocols),
            "matching_protocols": matching_protocols,
            "message": "✅ Режим соответствует клиническим рекомендациям" if regimen_found else "⚠️ Режим не найден в официальных рекомендациях"
        }
    
    def extract_treatments_with_ai(self, history: str) -> List[str]:
        """
        Использует DeepSeek для интеллектуального извлечения всех назначенных препаратов
        """
        print("\n💊 AI ИЗВЛЕКАЕТ НАЗНАЧЕННЫЕ ПРЕПАРАТЫ")
        
        try:
            prompt = f"""Проанализируй историю болезни и извлеки ВСЕ ПРОТИВООПУХОЛЕВЫЕ ПРЕПАРАТЫ, которые БЫЛИ НАЗНАЧЕНЫ пациенту.

История болезни:
{history[:3000]}

ВАЖНО: Извлеки ТОЛЬКО препараты, которые УЖЕ БЫЛИ ИСПОЛЬЗОВАНЫ в лечении (все линии терапии).

Правила расшифровки:
- TC, ТС = паклитаксел + карбоплатин
- XELOX = оксалиплатин + капецитабин  
- FOLFOX = оксалиплатин + 5-фторурацил + лейковорин
- FOLFIRI = иринотекан + 5-фторурацил + лейковорин
- AC = доксорубицин + циклофосфамид
- EDP-M = этопозид + доксорубицин + цисплатин + митотан
- ТС + трастузумаб = паклитаксел + карбоплатин + трастузумаб

Верни ТОЛЬКО JSON-массив строк с названиями препаратов.
Никакого дополнительного текста, только массив.

Примеры ответа:
["паклитаксел", "карбоплатин", "трастузумаб"]
["оксалиплатин", "капецитабин", "рамуцирумаб", "иринотекан"]
["цисплатин", "этопозид", "доксорубицин"]
[]
"""

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты - медицинский эксперт. Извлекаешь лекарственные препараты из текста. Отвечаешь только JSON-массивом."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"📥 AI ответ (извлечение): {content[:200]}...")
                
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                

                try:
                    treatments = json.loads(content)
                    if isinstance(treatments, list):
                        treatments = [str(t).strip().lower() for t in treatments if t and len(str(t).strip()) > 0]
                        print(f"✅ AI извлек {len(treatments)} препаратов: {treatments}")
                        
                        if not treatments:
                            print("⚠️ AI вернул пустой список, использую fallback")
                            return self._extract_treatments_fallback(history)
                            
                        return treatments
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    array_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
                    if array_match:
                        try:
                            array_str = array_match.group(0)
                            treatments = json.loads(array_str)
                            if isinstance(treatments, list):
                                treatments = [str(t).strip().lower() for t in treatments if t]
                                print(f"✅ AI извлек {len(treatments)} препаратов (из массива): {treatments}")
                                return treatments
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Ошибка при AI-извлечении препаратов: {e}")
        
        print("⚠️ Использую fallback-метод извлечения")
        return self._extract_treatments_fallback(history)
    
    def _extract_treatments_fallback(self, history: str) -> List[str]:
        """Улучшенный fallback с поддержкой контекста"""
        treatments = set()
        text = history.lower()
        
        regimens = {
            'tc': ['паклитаксел', 'карбоплатин'],
            'тс': ['паклитаксел', 'карбоплатин'],
            'xelox': ['оксалиплатин', 'капецитабин'],
            'capox': ['оксалиплатин', 'капецитабин'],
            'folfox': ['оксалиплатин', 'фторурацил', 'лейковорин'],
            'folfiri': ['иринотекан', 'фторурацил', 'лейковорин'],
            'folfirinox': ['оксалиплатин', 'иринотекан', 'фторурацил', 'лейковорин'],
            'ac': ['доксорубицин', 'циклофосфамид'],
            'ec': ['эпирубицин', 'циклофосфамид'],
            'edp-m': ['этопозид', 'доксорубицин', 'цисплатин', 'митотан'],
            'gp': ['гемцитабин', 'цисплатин'],
            'gc': ['гемцитабин', 'цисплатин'],
            'gemcarbo': ['гемцитабин', 'карбоплатин'],
        }
        
        for abbr, drugs in regimens.items():
            if abbr in text:
                print(f"  → Найдена аббревиатура '{abbr}': {drugs}")
                for drug in drugs:
                    treatments.add(drug)
        
        known_drugs = [
            'капецитабин', 'рамуцирумаб', 'паклитаксел', 'иринотекан',
            'оксалиплатин', 'фторурацил', 'лейковорин', 'гемцитабин',
            'цисплатин', 'карбоплатин', 'доцетаксел',
            'трастузумаб', 'трастузумаб дерукстекан', 'энхерту', 'пертузумаб', 'тукатиниб',
            'трастузумаб-эмтанзин', 'т-дм1',
            'осимертиниб', 'гефитиниб', 'эрлотиниб', 'алектиниб', 'кризотиниб',
            'церитиниб', 'дабрафениб', 'траметиниб', 'вемурафениб',
            'пембролизумаб', 'ниволумаб', 'атезолизумаб', 'ипилимумаб',
            'доксорубицин', 'эпирубицин',
            'циклофосфамид', 'ифосфамид', 'митомицин', 'митотан',
            'пеметрексед', 'винорельбин', 'эрибулин', 'этопозид',
            'винбластин', 'винкристин', 'блеомицин', 'метотрексат'
        ]
        
        for drug in known_drugs:
            if drug in text:
                treatments.add(drug)
        
        result = list(treatments)
        print(f"📊 Fallback извлек {len(result)} препаратов: {result}")
        return result
    
    def enhance_response_with_guidelines(self, patient_history: str, ai_response: dict, cancer_type: str = None, is_update: bool = False, precomputed_score: dict = None, treatment_lines: dict = None) -> dict:
        """
        Обогащает ответ данными из рекомендаций с правильным расчетом compliance_score
        """
        
        print("\n🔴🔴🔴 [AI_SERVICE] ОБОГАЩЕНИЕ ОТВЕТА 🔴🔴🔴")
        print(f"📥 Получен cancer_type: '{cancer_type}'")
        print(f"🔄 is_update: {is_update}")
        print(f"📊 precomputed_score передан: {'да' if precomputed_score else 'нет'}")
        print(f"📋 treatment_lines переданы: {'да' if treatment_lines else 'нет'}")
        
        detected_cancer_types = []
        
        if cancer_type and cancer_type != 'general':
            detected_cancer_types = [cancer_type]
            print(f"📊 Тип рака (передан): {cancer_type}")
        else:
            main_cancer_type = self.detect_cancer_type(patient_history)
            detected_cancer_types = [main_cancer_type]
            print(f"📊 Определенный тип рака: {main_cancer_type}")
        
        ai_response['cancer_type'] = detected_cancer_types[0] if detected_cancer_types else 'general'
        
        analysis_id = str(uuid.uuid4())
        ai_response['analysis_id'] = analysis_id
        ai_response['original_history'] = patient_history
        
        print(f"🆔 Сгенерирован analysis_id: {analysis_id}")
        
        print("\n📊 РАСЧЕТ COMPLIANCE SCORE...")
        

        if precomputed_score:
            score_result = precomputed_score
            print(f"✅ Использую переданный score: {score_result['score']}%")
            print(f"📌 Источник: {score_result.get('source', 'unknown')}")
        else:

            print("⚠️ Нет переданного score, рассчитываю самостоятельно")
            
            prescribed_treatments = self.extract_treatments_with_ai(patient_history)
            
            if not prescribed_treatments:
                print("⚠️ AI не извлек препараты, использую fallback")
                prescribed_treatments = self._extract_treatments_fallback(patient_history)
            
            print(f"💊 Извлеченные препараты для анализа: {prescribed_treatments}")
            
            biomarkers = self.extract_biomarkers(patient_history)
            
            if treatment_lines and treatment_lines.get('lines'):
                print(f"📋 Использую переданные линии терапии ({len(treatment_lines.get('lines', []))} линий)")
                score_result = scorer.calculate_score_from_protocols(
                    cancer_type=detected_cancer_types[0] if detected_cancer_types else 'general',
                    treatment_lines=treatment_lines,
                    biomarkers=biomarkers
                )
            else:
                print("⚠️ Нет линий терапии, использую старый метод расчета")
                score_result = scorer.calculate_score(
                    cancer_type=detected_cancer_types[0] if detected_cancer_types else 'general',
                    prescribed_treatments=prescribed_treatments,
                    biomarkers=biomarkers,
                    use_ai_fallback=True
                )
        
        print(f"✅ Итоговый score: {score_result['score']}%")
        print(f"📊 Детали: {score_result.get('message', '')}")
        
        if 'doctor_version' not in ai_response:
            ai_response['doctor_version'] = {}
        
        doctor = ai_response['doctor_version']
        
        doctor['compliance_score'] = score_result['score']
        doctor['compliance_details'] = {
            'score': score_result['score'],
            'findings': score_result.get('findings', []),
            'level': score_result.get('level', 'unknown'),
            'source': score_result.get('source', 'unknown'),
            'message': score_result.get('message', ''),
            'analyzed_lines': score_result.get('analyzed_lines', 0),
            'protocols_available': score_result.get('protocols_available', 0)
        }
        
        if score_result.get('source') == 'ai_fallback':
            doctor['kb_note'] = "⚠️ База знаний не содержит данных для этого типа рака. Оценка основана на AI. Рекомендуется ручная проверка в клинических рекомендациях."
        elif score_result.get('source') == 'ai_only':
            doctor['kb_note'] = "🤖 Для данного типа рака нет данных в базе Минздрава. Оценка основана на AI."
        elif score_result.get('source') == 'minzdrav_db':
            doctor['kb_note'] = "✅ Оценка основана на клинических рекомендациях Минздрава РФ"
        elif score_result.get('source') == 'mixed':
            doctor['kb_note'] = "🔄 Часть линий оценена по базе Минздрава, часть - AI"
        
        if treatment_lines:

            if isinstance(treatment_lines, dict):
                doctor['treatment_lines'] = treatment_lines.get('lines', [])
                doctor['planned_treatment'] = treatment_lines.get('planned')
            elif isinstance(treatment_lines, list):

                print("⚠️ treatment_lines передан как список, преобразую в словарь")
                doctor['treatment_lines'] = treatment_lines
                doctor['planned_treatment'] = None
            else:
                doctor['treatment_lines'] = []
                doctor['planned_treatment'] = None
            print(f"📋 Использую переданные линии терапии")
        else:

            print("⚠️ Линии терапии не переданы, извлекаю сейчас")
            extracted_lines = self.extract_treatment_lines(patient_history)
            doctor['treatment_lines'] = extracted_lines.get('lines', [])
            doctor['planned_treatment'] = extracted_lines.get('planned')
        

        if not precomputed_score:
            biomarkers = self.extract_biomarkers(patient_history)
            doctor['detected_biomarkers'] = {k: v for k, v in biomarkers.items() if v}
        

        from cancer_links import get_cancer_link
        from nccn_links import get_nccn_link
        from esmo_links import get_esmo_link
        
        primary_type = detected_cancer_types[0] if detected_cancer_types else 'general'
        
        minzdrav_link = get_cancer_link(primary_type)
        doctor['minzdrav_link'] = minzdrav_link
        
        doctor['international_guidelines'] = {
            'nccn': {
                'url': get_nccn_link(primary_type),
                'name': 'NCCN Clinical Practice Guidelines',
                'source': 'NCCN'
            },
            'esmo': {
                'url': get_esmo_link(primary_type),
                'name': 'ESMO Clinical Practice Guidelines',
                'source': 'ESMO'
            }
        }
        
        if self.knowledge_base:
            protocols = self.knowledge_base.get_protocols(primary_type)
            doctor['kb_protocols'] = protocols[:10]
            doctor['kb_total_protocols'] = len(protocols)
        
        if 'summary' in doctor:
            doctor['summary'] += f" {score_result['message']}"
        

        if not is_update:

            prescribed_for_missing = self.extract_treatments_with_ai(patient_history)
            biomarkers_for_missing = self.extract_biomarkers(patient_history)
            
            missing_info = self._check_missing_info_with_ai(
                patient_history,
                detected_cancer_types[0] if detected_cancer_types else 'general',
                ai_response,
                is_update=False,
                prescribed_treatments=prescribed_for_missing,
                biomarkers=biomarkers_for_missing
            )
            
            if missing_info:
                doctor['missing_info'] = missing_info
                print(f"⚠️ AI запросил уточнение информации: {len(missing_info.get('fields', []))} полей")
                print(f"   Из них влияют на score: {missing_info.get('has_score_impacting', False)}")
                
                score_impacting_fields = [f for f in missing_info.get('fields', []) if f.get('impacts_score')]
                if score_impacting_fields:
                    doctor['score_impacting_questions'] = [
                        {
                            'id': f['id'],
                            'question': f['question'],
                            'options': f.get('options', [])
                        }
                        for f in score_impacting_fields
                    ]
            else:
                print("✅ AI считает, что информации достаточно")
        else:
            print("✅ Это обновление анализа, убираем missing_info если было")
            if 'missing_info' in doctor:
                del doctor['missing_info']
            if 'score_impacting_questions' in doctor:
                del doctor['score_impacting_questions']

        if 'patient_version' in ai_response:
            patient = ai_response['patient_version']
            score = doctor.get('compliance_score', 0)
            
            if len(detected_cancer_types) > 1:
                cancer_names = [self._format_cancer_type_ru(t) for t in detected_cancer_types]
                patient['diagnosis_summary'] = f"Обнаружено несколько диагнозов: {', '.join(cancer_names)}"
            else:
                patient['diagnosis_summary'] = self._format_cancer_type_ru(primary_type)
            
            lines_count = len(doctor.get('treatment_lines', []))
            if lines_count > 0:
                patient['lines_info'] = f"Проведено линий терапии: {lines_count}"
            
            if score >= 90:
                patient['standard_compliance'] = {
                    'level': 'excellent',
                    'color': 'purple',
                    'icon': '🌟',
                    'text': 'Идеальное соответствие',
                    'explanation': f'Ваше лечение на {score}% соответствует самым строгим клиническим рекомендациям.'
                }
            elif score >= 80:
                patient['standard_compliance'] = {
                    'level': 'high',
                    'color': 'green',
                    'icon': '✅',
                    'text': 'Отличное соответствие',
                    'explanation': f'Ваше лечение на {score}% соответствует современным стандартам.'
                }
            elif score >= 70:
                patient['standard_compliance'] = {
                    'level': 'good',
                    'color': 'teal',
                    'icon': '✓',
                    'text': 'Хорошее соответствие',
                    'explanation': f'Лечение на {score}% соответствует рекомендациям. Есть незначительные отклонения.'
                }
            elif score >= 60:
                patient['standard_compliance'] = {
                    'level': 'medium',
                    'color': 'amber',
                    'icon': '⚠️',
                    'text': 'Среднее соответствие',
                    'explanation': f'Лечение соответствует стандартам на {score}%. Требуется обсуждение с врачом.'
                }
            elif score >= 40:
                patient['standard_compliance'] = {
                    'level': 'low',
                    'color': 'orange',
                    'icon': '❌',
                    'text': 'Низкое соответствие',
                    'explanation': f'Лечение соответствует стандартам только на {score}%. Есть существенные отклонения.'
                }
            else:
                patient['standard_compliance'] = {
                    'level': 'critical',
                    'color': 'red',
                    'icon': '🚨',
                    'text': 'Критическое несоответствие',
                    'explanation': f'Лечение соответствует стандартам лишь на {score}%. Требуется срочная консультация онколога.'
                }
            
            compliant = []
            warnings = []
            
            findings = score_result.get('findings', [])
            for finding in findings:
                treatment = finding.get('treatment', '')
                status = finding.get('status', '')
                comment = finding.get('comment', '')
                line = finding.get('line', '')
                
                line_info = f" (линия {line})" if line and line != 'planned' else " (планируется)" if line == 'planned' else ""
                
                if status == 'correct':
                    compliant.append(f"✓ {treatment}{line_info}: {comment}")
                elif status == 'warning' or status == 'info':
                    warnings.append(f"⚠️ {treatment}{line_info}: {comment}")
                elif status == 'critical':
                    warnings.append(f"❌ {treatment}{line_info}: {comment}")
            
            patient['compliant_treatments'] = compliant[:5]
            patient['treatment_warnings'] = warnings[:3]
            
            if doctor.get('minzdrav_link'):
                patient['minzdrav_link'] = doctor['minzdrav_link']
                patient['minzdrav_text'] = 'Что говорят официальные рекомендации Минздрава'
            
            if doctor.get('international_guidelines'):
                patient['international_guidelines'] = doctor['international_guidelines']
            
            if doctor.get('missing_info'):
                questions = []
                for field in doctor['missing_info'].get('fields', [])[:3]:
                    questions.append(field['question'])
                if questions:
                    patient['questions_for_doctor'] = questions
        
        print("🔴🔴🔴 ОБОГАЩЕНИЕ ЗАВЕРШЕНО 🔴🔴🔴\n")
        return ai_response

    def _format_cancer_type_ru(self, cancer_type: str) -> str:
        """Форматирует тип рака для отображения на русском"""
        types = {
            'breast': 'рак молочной железы',
            'lung': 'рак легкого',
            'colon': 'рак ободочной кишки',
            'rectal': 'рак прямой кишки',
            'prostate': 'рак предстательной железы',
            'pancreatic': 'рак поджелудочной железы',
            'esophageal': 'рак пищевода',
            'stomach': 'рак желудка',
            'liver': 'рак печени',
            'kidney': 'рак почки',
            'bladder': 'рак мочевого пузыря',
            'ovarian': 'рак яичников',
            'cervical': 'рак шейки матки',
            'uterine': 'рак матки',
            'melanoma': 'меланома',
            'head_neck': 'рак головы и шеи',
            'thyroid': 'рак щитовидной железы',
            'brain': 'опухоль головного мозга',
            'soft_tissue_sarcoma': 'саркома мягких тканей',
            'bone_sarcoma': 'саркома кости',
            'gist': 'GIST',
            'anal': 'рак анального канала',
            'testicular': 'рак яичка',
            'cancer_unknown_primary': 'CUP (неизвестный первичный очаг)',
            'general': 'злокачественное новообразование'
        }
        return types.get(cancer_type, cancer_type)
    
    def extract_biomarkers(self, text: str) -> Dict[str, any]:
        """
        Извлекает информацию о биомаркерах из текста
        """
        biomarkers = {
            'her2_positive': False,
            'her2_negative': False,
            'her2_status': None,
            'egfr_mutated': False,
            'alk_positive': False,
            'ros1_positive': False,
            'braf_mutated': False,
            'pd_l1_high': False,
            'msi_status': None,
            'tp53_mutated': False,
            'mss': False,
            'cup': False,
            'triple_negative': False
        }
        
        text_lower = text.lower()
        
        if any(p in text_lower for p in ['her2+', 'her2-положительн', 'her2 позитивн', 'her2 3+', 'erbb2 амплификация']):
            biomarkers['her2_positive'] = True
            biomarkers['her2_status'] = 'positive'
        elif any(p in text_lower for p in ['her2-', 'her2-отрицательн', 'her2 негативн', 'her2 0', 'her2 1+']):
            biomarkers['her2_negative'] = True
            biomarkers['her2_status'] = 'negative'
        
        if any(p in text_lower for p in ['egfr мутац', 'egfr+', 'egfr-положительн', 'egfr mut', 'egfrmut', 'egfr мутация']):
            biomarkers['egfr_mutated'] = True
        
        if any(p in text_lower for p in ['alk+', 'alk-положительн', 'alk позитивн']):
            biomarkers['alk_positive'] = True
        
        if any(p in text_lower for p in ['ros1+', 'ros1-положительн', 'ros1 позитивн']):
            biomarkers['ros1_positive'] = True
        
        if any(p in text_lower for p in ['braf мутац', 'braf v600e']):
            biomarkers['braf_mutated'] = True
        
        if any(p in text_lower for p in ['pd-l1 ≥50', 'pd-l1 >50', 'pd-l1 высок', 'pdl1 высок']):
            biomarkers['pd_l1_high'] = True
        
        if 'msi-h' in text_lower or 'msi высок' in text_lower:
            biomarkers['msi_status'] = 'high'
        elif 'mss' in text_lower:
            biomarkers['mss'] = True
            biomarkers['msi_status'] = 'stable'
        
        if 'tp53' in text_lower or 'p53' in text_lower:
            biomarkers['tp53_mutated'] = True
        
        if any(p in text_lower for p in ['невыявленного первичного', 'неизвестного первичного', 'cup', 'онпл']):
            biomarkers['cup'] = True
        
        if any(p in text_lower for p in ['трижды негативн', 'тройной негативн']):
            biomarkers['triple_negative'] = True
            biomarkers['her2_negative'] = True
        
        print(f"📊 Извлеченные биомаркеры: {biomarkers}")
        return biomarkers
    
    def _check_missing_info_with_ai(self, history: str, cancer_type: str, ai_response: dict, is_update: bool = False, prescribed_treatments: List[str] = None, biomarkers: Dict = None) -> Optional[Dict]:
        """
        AI анализирует, какой информации не хватает для полного анализа
        """
        print("\n" + "="*60)
        print("🔍 AI АНАЛИЗИРУЕТ НЕДОСТАЮЩУЮ ИНФОРМАЦИЮ")
        print("="*60)
        
        if is_update:
            print("✅ Это обновление - пропускаем запрос информации")
            return None
        
        if prescribed_treatments is None:
            prescribed_treatments = self.extract_treatments_with_ai(history)
        if biomarkers is None:
            biomarkers = self.extract_biomarkers(history)
        
        max_retries = 3
        timeout = 30
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 Повторная попытка {attempt}...")
                    timeout += 10
                    strict_warning = "\n\nПРЕДЫДУЩАЯ ПОПЫТКА ВЕРНУЛА НЕВАЛИДНЫЙ JSON. УБЕДИСЬ, ЧТО JSON КОРРЕКТЕН! НИКАКОГО ТЕКСТА ДО И ПОСЛЕ JSON."
                else:
                    strict_warning = ""
                
                prompt = f"""Ты - опытный онколог. Проанализируй историю болезни и определи, какой информации не хватает.

История болезни:
{history[:2000]}

Тип рака: {cancer_type}
Назначенные препараты: {prescribed_treatments}
Выявленные биомаркеры: {json.dumps(biomarkers, ensure_ascii=False)}

{strict_warning}

ВАЖНО: Раздели вопросы на ДВА ТИПА:

1. **ВЛИЯЮТ НА ВЫБОР ЛЕЧЕНИЯ (меняют compliance_score)**:
   - Какие конкретные препараты планируются в следующей линии?
   - Изменилась ли схема лечения?
   - Появились ли новые мутации/биомаркеры?
   - Была ли повторная биопсия, изменившая молекулярный профиль?

2. **КОНТЕКСТНЫЕ (НЕ влияют на score, но важны для прогноза)**:
   - ECOG статус / общее состояние
   - Детали гистологии (степень дифференцировки)
   - Объем предшествующих операций
   - PD-L1 статус (если не влияет на выбор терапии)
   - Сопутствующие заболевания
   - Переносимость предыдущей терапии

Верни ТОЛЬКО JSON. НИКАКОГО ТЕКСТА ДО И ПОСЛЕ JSON:

{{
    "has_missing_info": true/false,
    "message": "общее сообщение о недостающей информации на русском",
    "fields": [
        {{
            "id": "уникальный_id",
            "question": "вопрос на русском",
            "description": "почему это важно",
            "type": "select",
            "options": ["вариант 1", "вариант 2", "вариант 3"],
            "required": true,
            "impacts_score": true,
            "impacts_recommendations": true,
            "category": "treatment/prognosis/biomarker/diagnostic"
        }}
    ]
}}

Если информации достаточно - has_missing_info: false и fields: []
"""

                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "Ты - медицинский эксперт. Отвечаешь ТОЛЬКО валидным JSON, без пояснений и markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"}
                }
                
                response = requests.post(
                    self.deepseek_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code != 200:
                    print(f"❌ Статус ошибки: {response.status_code}")
                    continue
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                
                content = re.sub(r'[\x00-\x1F\x7F]', '', content)
                
                try:
                    missing_info = json.loads(content)
                    
                    if not isinstance(missing_info, dict):
                        print("❌ Ответ не является объектом JSON")
                        continue
                    
                    if missing_info.get('has_missing_info'):
                        fields = missing_info.get('fields', [])
                        if not isinstance(fields, list):
                            fields = []
                        
                        valid_fields = []
                        for field in fields:
                            if isinstance(field, dict) and field.get('id') and field.get('question'):
                                field.setdefault('impacts_score', False)
                                field.setdefault('impacts_recommendations', True)
                                field.setdefault('required', True)
                                field.setdefault('type', 'select')
                                field.setdefault('options', ['Да', 'Нет', 'Неизвестно'])
                                field.setdefault('category', 'general')
                                valid_fields.append(field)
                        
                        valid_fields = valid_fields[:5]
                        
                        print(f"🔍 Найдено {len(valid_fields)} полей для уточнения")
                        print(f"   Из них влияют на score: {sum(1 for f in valid_fields if f.get('impacts_score'))}")
                        
                        return {
                            "required": True,
                            "message": missing_info.get('message', 'Для точного анализа необходима дополнительная информация'),
                            "fields": valid_fields,
                            "total_fields": len(valid_fields),
                            "has_score_impacting": any(f.get('impacts_score') for f in valid_fields)
                        }
                    else:
                        print("✅ AI считает, что информации достаточно")
                        return None
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    continue
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                continue
        
        print("⚠️ Не удалось получить корректный JSON от AI после всех попыток")
        return self._fallback_missing_info(cancer_type, prescribed_treatments, biomarkers)
    
    def _fallback_missing_info(self, cancer_type: str, treatments: List[str], biomarkers: Dict) -> Dict:
        """
        Запасной вариант вопросов, если AI не сработал
        """
        print("📋 Использую запасной набор вопросов")
        
        fields = []
        
        fields.append({
            "id": "planned_treatment",
            "question": "Какие препараты планируются для следующей линии терапии?",
            "description": "Это критически важно для оценки соответствия стандартам",
            "type": "textarea",
            "required": True,
            "impacts_score": True,
            "impacts_recommendations": True,
            "category": "treatment"
        })
        
        fields.append({
            "id": "ecog_status",
            "question": "Каково общее состояние пациента (ECOG)?",
            "description": "Влияет на переносимость терапии и прогноз",
            "type": "select",
            "options": ["ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3", "ECOG 4"],
            "required": True,
            "impacts_score": False,
            "impacts_recommendations": True,
            "category": "prognosis"
        })
        
        if cancer_type == 'cancer_unknown_primary':
            fields.append({
                "id": "ihc_markers",
                "question": "Какие дополнительные ИГХ маркеры были исследованы?",
                "description": "Расширенная ИГХ-панель помогает определить первичный очаг",
                "type": "multiselect",
                "options": [
                    "TTF-1 (легкие)",
                    "CDX2/CK20 (ЖКТ)",
                    "GATA3/Mammaglobin (молочная железа)",
                    "PAX8/RCC (почки)",
                    "Thyroglobulin (щитовидная железа)",
                    "PSA (простата)",
                    "Не проводилось"
                ],
                "required": False,
                "impacts_score": True,
                "impacts_recommendations": True,
                "category": "diagnostic"
            })
        
        if biomarkers.get('her2_positive'):
            fields.append({
                "id": "her2_therapy_type",
                "question": "Какой тип анти-HER2 терапии планируется?",
                "description": "Выбор зависит от предшествующей терапии и прогрессии",
                "type": "select",
                "options": [
                    "Трастузумаб-эмтансин (T-DM1)",
                    "Трастузумаб дерукстекан",
                    "Трастузумаб + пертузумаб",
                    "Тукатиниб + трастузумаб",
                    "Продолжение текущей терапии"
                ],
                "required": True,
                "impacts_score": True,
                "impacts_recommendations": True,
                "category": "treatment"
            })
        
        if biomarkers.get('egfr_mutated'):
            fields.append({
                "id": "t790m_status",
                "question": "Определялся ли статус T790M после прогрессии?",
                "description": "Ключевой фактор для выбора дальнейшей терапии",
                "type": "select",
                "options": ["T790M положительный", "T790M отрицательный", "Не определялся"],
                "required": True,
                "impacts_score": True,
                "impacts_recommendations": True,
                "category": "biomarker"
            })
        
        fields = fields[:5]
        
        return {
            "required": True,
            "message": "Для более точного анализа необходима дополнительная информация",
            "fields": fields,
            "total_fields": len(fields),
            "has_score_impacting": any(f.get('impacts_score') for f in fields),
            "source": "fallback"
        }


ai_service = AIService()