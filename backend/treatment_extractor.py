
import json
import re
import requests
from typing import Dict, List, Any, Optional

class TreatmentLineExtractor:
    """
    Извлекает линии терапии из истории болезни с помощью AI
    """
    
    def __init__(self, deepseek_api_key: str):
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
    
    def extract_lines(self, history: str) -> Dict[str, Any]:
        """
        Извлекает все линии терапии из истории
        Всегда возвращает словарь с ключами 'lines' и 'planned'
        """
        print("\n📋 ИЗВЛЕЧЕНИЕ ЛИНИЙ ТЕРАПИИ")
        

        default_result = {"lines": [], "planned": None}
        
        try:
            prompt = f"""Ты - опытный онколог. Проанализируй историю болезни и извлеки ВСЕ линии противоопухолевой терапии.

История болезни:
{history[:4000]}

ПРАВИЛА ИЗВЛЕЧЕНИЯ:
1. Найди каждую линию терапии (1 линия, 2 линия, поддерживающая, неоадъювантная, адъювантная)
2. Для каждой линии укажи ВСЕ препараты в этой комбинации
3. Расшифруй аббревиатуры:
   - TC, ТС = паклитаксел + карбоплатин
   - XELOX = оксалиплатин + капецитабин
   - FOLFOX = оксалиплатин + фторурацил + лейковорин
   - FOLFIRI = иринотекан + фторурацил + лейковорин
   - AC = доксорубицин + циклофосфамид
4. Укажи период лечения (если есть)
5. Укажи ответ на лечение (прогрессирование, стабилизация, ремиссия)
6. Отдельно выдели планируемое/рекомендованное лечение

Верни ТОЛЬКО JSON в формате:
{{
    "lines": [
        {{
            "line": 1,
            "name": "первая линия / неоадъювантная / адъювантная",
            "treatments": ["препарат1", "препарат2"],
            "period": "дата начала - дата окончания",
            "response": "прогрессирование/стабилизация/ремиссия",
            "notes": "дополнительная информация"
        }}
    ],
    "planned": {{
        "treatments": ["препарат1", "препарат2"],
        "description": "планируемая терапия",
        "source": "рекомендация консилиума / решение врача"
    }}
}}

Если информации о линиях нет, верни {{"lines": []}}
"""

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты - медицинский эксперт. Извлекаешь линии терапии из текста. Отвечаешь только JSON."},
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
                    lines_data = json.loads(content)

                    if not isinstance(lines_data, dict):
                        return default_result
                    if 'lines' not in lines_data:
                        lines_data['lines'] = []
                    if 'planned' not in lines_data:
                        lines_data['planned'] = None
                    return lines_data
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    return default_result
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return default_result
                
        except Exception as e:
            print(f"❌ Ошибка при извлечении линий: {e}")
            return default_result
    
    def extract_lines_fallback(self, history: str) -> Dict[str, Any]:
        """
        Запасной метод извлечения линий через регулярные выражения
        Всегда возвращает словарь с ключами 'lines' и 'planned'
        """
        lines = []
        text = history.lower()
        

        line_patterns = [
            (r'(\d+)\s*линия\s*[:\s]*([^\.]+)', 'line'),
            (r'первая\s*линия\s*[:\s]*([^\.]+)', 'first'),
            (r'вторая\s*линия\s*[:\s]*([^\.]+)', 'second'),
            (r'третья\s*линия\s*[:\s]*([^\.]+)', 'third'),
            (r'неоадъювантн[ая]+[^:]*:\s*([^\.]+)', 'neoadjuvant'),
            (r'адъювантн[ая]+[^:]*:\s*([^\.]+)', 'adjuvant'),
            (r'поддерживающ[ая]+[^:]*:\s*([^\.]+)', 'maintenance'),
        ]
        

        regimen_map = {
            'tc': ['паклитаксел', 'карбоплатин'],
            'тс': ['паклитаксел', 'карбоплатин'],
            'xelox': ['оксалиплатин', 'капецитабин'],
            'capox': ['оксалиплатин', 'капецитабин'],
            'folfox': ['оксалиплатин', 'фторурацил', 'лейковорин'],
            'folfiri': ['иринотекан', 'фторурацил', 'лейковорин'],
            'ac': ['доксорубицин', 'циклофосфамид'],
        }
        

        for pattern, line_type in line_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    line_num, treatment_text = match
                else:
                    treatment_text = match
                    line_num = line_type
                

                treatments = []
                

                for abbr, drugs in regimen_map.items():
                    if abbr in treatment_text:
                        treatments.extend(drugs)
                

                if not treatments:
                    known_drugs = [
                        'паклитаксел', 'карбоплатин', 'цисплатин', 'гемцитабин',
                        'трастузумаб', 'рамуцирумаб', 'иринотекан', 'доцетаксел',
                        'капецитабин', 'оксалиплатин', 'фторурацил', 'этопозид',
                        'доксорубицин', 'циклофосфамид', 'метотрексат', 'винорельбин',
                        'эрибулин', 'пембролизумаб', 'ниволумаб', 'атезолизумаб',
                        'бевацизумаб', 'осимертиниб', 'алектиниб', 'кризотиниб'
                    ]
                    for drug in known_drugs:
                        if drug in treatment_text:
                            treatments.append(drug)
                
                if treatments:
                    lines.append({
                        'line': len(lines) + 1,
                        'name': f"{line_type} линия",
                        'treatments': list(set(treatments)),
                        'response': 'неизвестно'
                    })
        
        return {"lines": lines, "planned": None}