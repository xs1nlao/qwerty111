
import json
import os
from typing import Dict, List, Any
from glob import glob

class KnowledgeBaseLoader:
    """
    Загружает и объединяет все запарсенные файлы клинических рекомендаций
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        else:
            self.data_dir = data_dir
            
        self.guidelines = {}
        self.protocols_cache = {} 
        self.rules_cache = {}      
        print(f"📁 Папка с базой знаний: {self.data_dir}")
        self.load_all_guidelines()
    
    def load_all_guidelines(self):
        """Загружает все JSON файлы с рекомендациями"""
        print("\n📚 ЗАГРУЗКА БАЗЫ ЗНАНИЙ МИНЗДРАВА")
        
        if not os.path.exists(self.data_dir):
            print(f"❌ Папка {self.data_dir} не существует!")
            os.makedirs(self.data_dir, exist_ok=True)
            return
        
        json_files = glob(os.path.join(self.data_dir, "*.json"))
        print(f"🔍 Найдено файлов: {len(json_files)}")
        
        if not json_files:
            print("⚠️ Нет файлов для загрузки!")
            return
        
        loaded_count = 0
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = os.path.basename(file_path)
                cancer_type = filename.replace('_parsed.json', '').replace('.json', '')
                type_key = self._map_filename_to_type(cancer_type)
                
                self.guidelines[type_key] = {
                    'file': filename,
                    'data': data,
                    'name': data.get('document_info', {}).get('title', filename),
                    'source': 'Минздрав РФ',
                    'loaded': True
                }
                

                protocols = self._extract_protocols_from_data(data, type_key)
                if protocols:
                    self.protocols_cache[type_key] = protocols
                
                loaded_count += 1
                print(f"✅ Загружен: {type_key} -> {filename} (протоколов: {len(protocols)})")
                
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка JSON в {file_path}: {e}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {file_path}: {e}")
        
        print(f"\n✅ ВСЕГО ЗАГРУЖЕНО: {loaded_count} рекомендаций")
        print(f"📊 Всего протоколов в кэше: {sum(len(p) for p in self.protocols_cache.values())}")
    
    def _extract_protocols_from_data(self, data: Dict, cancer_type: str) -> List[Dict]:
        """Извлекает протоколы из данных"""
        protocols = []
        

        if 'treatment_protocols' in data:
            for p in data['treatment_protocols']:
                protocols.append({
                    'protocol_name': p.get('protocol_name', ''),
                    'condition': p.get('condition', ''),
                    'stage': p.get('stage', ''),
                    'medications': p.get('medications', []),
                    'treatment_steps': p.get('treatment_steps', []),
                    'source': data.get('document_info', {}).get('title', ''),
                    'cancer_type': cancer_type
                })
        

        if 'clinical_recommendations' in data:
            recs = data['clinical_recommendations']
            if 'specific' in recs and isinstance(recs['specific'], list):
                for rec in recs['specific']:
                    if isinstance(rec, str) and any(drug in rec.lower() for drug in ['химиотерапия', 'таргетная', 'иммунотерапия']):
                        protocols.append({
                            'protocol_name': 'Рекомендация',
                            'condition': 'Общая рекомендация',
                            'medications': self._extract_drugs_from_text(rec),
                            'source': data.get('document_info', {}).get('title', ''),
                            'cancer_type': cancer_type
                        })
        
        return protocols
    
    def _extract_drugs_from_text(self, text: str) -> List[str]:
        """Извлекает названия препаратов из текста"""
        known_drugs = [
            'паклитаксел', 'карбоплатин', 'цисплатин', 'гемцитабин',
            'трастузумаб', 'осимертиниб', 'пеметрексед', 'атезолизумаб',
            'бевацизумаб', 'рамуцирумаб', 'иринотекан', 'доцетаксел',
            'эрибулин', 'винорельбин', 'капецитабин', 'метотрексат',
            'циклофосфамид', 'доксорубицин', 'тамоксифен', 'летрозол',
            'анастрозол', 'кризотиниб', 'алектиниб', 'церитиниб',
            'пембролизумаб', 'ниволумаб', 'ипилимумаб', 'тукатиниб'
        ]
        
        found = []
        text_lower = text.lower()
        for drug in known_drugs:
            if drug in text_lower:
                found.append(drug)
        
        return found
    
    def _map_filename_to_type(self, filename: str) -> str:
        """Преобразует имя файла в тип рака для нашей системы"""
        mapping = {
            'adrenal_cancer': 'adrenal',
            'anal_cancer': 'anal',
            'bladder_cancer': 'bladder',
            'bone_sarcoma_parsed': 'bone_sarcoma',
            'brain_metastasis': 'brain',
            'breast_cancer': 'breast',
            'cancer_unknown_primary': 'cancer_unknown_primary',
            'cervical_cancer_neck': 'cervical',
            'cns_tumors': 'brain',
            'colon_cancer': 'colon',
            'esophageal_cancer': 'esophageal',
            'germ_cell_male': 'testicular',
            'gist_parsed': 'gist',
            'hypopharynx_cancer': 'hypopharynx',
            'kidney_cancer': 'kidney',
            'kidney_parenchyma_cancer': 'kidney',
            'laryngeal_cancer': 'laryngeal',
            'lip_cancer': 'lip',
            'liver_cancer': 'liver',
            'lung_cancer': 'lung',
            'lymphoid_cancer': 'lymphoma',
            'mediastinal_tumors': 'mediastinal_tumors',
            'melanoma': 'melanoma',
            'merkel_cell_carcinoma': 'merkel_cell',
            'mesothelioma': 'mesothelioma',
            'nasal_cancer': 'nasal',
            'nasopharyngeal_cancer': 'nasopharyngeal',
            'oral_cavity_cancer': 'oral_cavity',
            'oropharynx_cancer': 'oropharynx',
            'ovarian_borderline': 'ovarian_borderline',
            'ovarian_cancer': 'ovarian',
            'ovarian_nonepithelial': 'ovarian_nonepithelial',
            'pancreatic_cancer': 'pancreatic',
            'penile_cancer': 'penile',
            'prostate_cancer': 'prostate',
            'rectal_cancer': 'rectal',
            'retroperitoneal_sarcoma': 'retroperitoneal_sarcoma',
            'salivary_glands_cancer': 'salivary_glands',
            'skin_bcc': 'skin_bcc',
            'skin_scc': 'skin_scc',
            'stomach_cancer': 'stomach',
            'testicular_cancer': 'testicular',
            'thyroid_diff_cancer': 'thyroid'
        }
        return mapping.get(filename, filename)
    
    def get_guideline(self, cancer_type: str) -> Dict[str, Any]:
        """Возвращает рекомендации для конкретного типа рака"""
        return self.guidelines.get(cancer_type, {}).get('data', {})
    
    def get_protocols(self, cancer_type: str) -> List[Dict[str, Any]]:
        """Возвращает протоколы для конкретного типа рака"""
        return self.protocols_cache.get(cancer_type, [])
    
    def create_rules_for_scoring(self, cancer_type: str) -> Dict[str, Any]:
        """
        Улучшенное создание правил для scoring.py на основе загруженных рекомендаций
        """
        if cancer_type in self.rules_cache:
            return self.rules_cache[cancer_type]
        
        protocols = self.get_protocols(cancer_type)
        if not protocols:
            return {}
        
        rules = {}
        
        for protocol in protocols:
            condition = protocol.get('condition', '').lower()
            protocol_name = protocol.get('protocol_name', '').lower()
            medications = protocol.get('medications', [])
            

            if isinstance(medications, list):
                meds_list = [str(m).lower() for m in medications if m]
            else:
                meds_list = []
            

            biomarkers = self._extract_biomarkers_from_text(condition + " " + protocol_name)
            

            if not biomarkers:
                biomarkers = ['general']
            

            for biomarker in biomarkers:
                if biomarker not in rules:
                    rules[biomarker] = {
                        'correct': [],
                        'warning': [],
                        'critical': []
                    }
                

                for med in meds_list:
                    if med not in rules[biomarker]['correct']:
                        rules[biomarker]['correct'].append(med)
        

        for biomarker in rules:
            rules[biomarker]['correct'] = list(set(rules[biomarker]['correct']))
        

        self._add_contraindications(rules, cancer_type)

        self.rules_cache[cancer_type] = rules
        print(f"  → Создано правил для {cancer_type}: {len(rules)} наборов")
        
        return rules
    
    def _extract_biomarkers_from_text(self, text: str) -> List[str]:
        """Извлекает биомаркеры из текста условия"""
        biomarkers = []
        text_lower = text.lower()
        
        biomarker_keywords = {
            'her2_positive': ['her2+', 'her2-положительн', 'her2 позитивн', 'her2 overexpressing', 'her2 3+'],
            'her2_negative': ['her2-', 'her2-отрицательн', 'her2 негативн', 'her2 0', 'her2 1+'],
            'egfr_mutated': ['egfr мутац', 'egfr+', 'egfr mut', 'egfr mutated'],
            'alk_positive': ['alk+', 'alk-положительн', 'alk позитивн', 'alk rearrangement'],
            'ros1_positive': ['ros1+', 'ros1 rearrangement'],
            'braf_mutated': ['braf мутац', 'braf v600e', 'braf mutated'],
            'pd_l1_high': ['pd-l1 ≥50', 'pd-l1 high', 'pdl1 high', 'pd-l1 >50%'],
            'msi_high': ['msi-h', 'msi высок', 'microsatellite instability-high'],
            'mss': ['mss', 'microsatellite stable'],
            'triple_negative': ['трижды негативн', 'тройной негативн', 'triple negative'],
            'tp53_mutated': ['tp53', 'p53 мутация'],
            'brca_mutated': ['brca мутация', 'brca1', 'brca2']
        }
        
        for biomarker, keywords in biomarker_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    biomarkers.append(biomarker)
                    break
        
        return list(set(biomarkers))
    
    def _add_contraindications(self, rules: Dict, cancer_type: str):
        """Добавляет известные противопоказания в правила"""
        

        if cancer_type in ['breast', 'stomach', 'cancer_unknown_primary']:
            if 'her2_negative' in rules:
                rules['her2_negative']['critical'] = ['трастузумаб', 'trastuzumab', 'пертузумаб', 'pertuzumab', 'тукатиниб', 'tucatinib']
        

        if cancer_type == 'lung':
            if 'egfr_mutated' not in rules and 'general' in rules:
                rules['general']['warning'] = rules['general'].get('warning', []) + ['гефитиниб', 'gefitinib', 'эрлотиниб', 'erlotinib']
        

        if 'triple_negative' in rules:
            rules['triple_negative']['critical'] = ['тамоксифен', 'tamoxifen', 'летрозол', 'letrozole', 'анастрозол', 'anastrozole']
    
    def get_all_rules(self) -> Dict[str, Any]:
        """Возвращает правила для всех типов рака"""
        if not self.rules_cache:
            for cancer_type in self.guidelines.keys():
                self.create_rules_for_scoring(cancer_type)
        return self.rules_cache
    
    def index_protocols_by_line(self):
        """
        Индексирует протоколы по линиям терапии для быстрого поиска
        """
        self.protocols_by_line = {
            'first_line': [],
            'second_line': [],
            'third_line': [],
            'adjuvant': [],
            'neoadjuvant': [],
            'metastatic': []
        }
        
        for cancer_type, protocols in self.protocols_cache.items():
            for protocol in protocols:
                line = self._detect_protocol_line(protocol)
                protocol['cancer_type'] = cancer_type
                self.protocols_by_line[line].append(protocol)
        
        print(f"\n📊 Проиндексировано протоколов:")
        for line, prots in self.protocols_by_line.items():
            print(f"   {line}: {len(prots)}")



kb_loader = KnowledgeBaseLoader()