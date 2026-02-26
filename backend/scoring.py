
import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from glob import glob


class ComplianceScorer:
    """
    Расчет compliance_score на основе базы Минздрава с AI-дополнением
    """
    
    def __init__(self):
        self.max_score = 100
        self.max_score_per_treatment = 25
        self.protocols_db = {}  
        self.line_weights = {
            'first_line': 1.0,    
            'second_line': 0.9,     
            'third_line': 0.8,    
            'fourth_plus': 0.7,     
            'planned': 0.85,        
            'adjuvant': 0.95,        
            'neoadjuvant': 0.95,    
            'metastatic': 0.8       
        }
        

        self.drug_families = {

            'трастузумаб': ['трастузумаб', 'герцептин', 'trastuzumab'],
            'трастузумаб дерукстекан': ['трастузумаб дерукстекан', 'энхерту', 'tdxd', 'trastuzumab deruxtecan', 'трастузумаб'],
            'трастузумаб-эмтансин': ['трастузумаб-эмтансин', 'т-дм1', 't-dm1', 'кадсила', 'трастузумаб'],
            'пертузумаб': ['пертузумаб', 'перьета', 'pertuzumab'],
            'тукатиниб': ['тукатиниб', 'tukysa', 'tucatinib'],
            

            'паклитаксел': ['паклитаксел', 'taxol', 'paclitaxel', 'таксан'],
            'доцетаксел': ['доцетаксел', 'taxotere', 'docetaxel', 'таксан'],
            

            'карбоплатин': ['карбоплатин', 'carboplatin', 'платина'],
            'цисплатин': ['цисплатин', 'cisplatin', 'платина'],
            'оксалиплатин': ['оксалиплатин', 'oxaliplatin', 'платина'],
            

            'капецитабин': ['капецитабин', 'кселода', 'capecitabine'],
            'фторурацил': ['фторурацил', '5fu', '5-фторурацил', 'fluorouracil'],
            

            'иринотекан': ['иринотекан', 'camptosar', 'irinotecan'],
            

            'рамуцирумаб': ['рамуцирумаб', 'цирамза', 'ramucirumab'],
            'бевацизумаб': ['бевацизумаб', 'авастин', 'bevacizumab'],
            

            'гефитиниб': ['гефитиниб', 'иресса', 'gefitinib'],
            'эрлотиниб': ['эрлотиниб', 'тарцева', 'erlotinib'],
            'осимертиниб': ['осимертиниб', 'тагрессо', 'osimertinib'],
            

            'алектиниб': ['алектиниб', 'алеценза', 'alectinib'],
            'кризотиниб': ['кризотиниб', 'ксалкори', 'crizotinib'],
            'церитиниб': ['церитиниб', 'зикадия', 'ceritinib'],
            

            'дабрафениб': ['дабрафениб', 'тафинлар', 'dabrafenib'],
            'траметиниб': ['траметиниб', 'мекинист', 'trametinib'],
            'вемурафениб': ['вемурафениб', 'зельбораф', 'vemurafenib'],
            

            'пембролизумаб': ['пембролизумаб', 'кейтруда', 'pembrolizumab'],
            'ниволумаб': ['ниволумаб', 'опдиво', 'nivolumab'],
            'атезолизумаб': ['атезолизумаб', 'тецентрик', 'atezolizumab'],
            

            'доксорубицин': ['доксорубицин', 'адриамицин', 'doxorubicin'],
            'эпирубицин': ['эпирубицин', 'epirubicin'],
            

            'циклофосфамид': ['циклофосфамид', 'cyclophosphamide'],
            'ифосфамид': ['ифосфамид', 'ifosfamide'],
            'митомицин': ['митомицин', 'mitomycin'],
            'митотан': ['митотан', 'mitotane'],
            

            'тамоксифен': ['тамоксифен', 'tamoxifen'],
            'летрозол': ['летрозол', 'letrozole', 'фемара'],
            'анастрозол': ['анастрозол', 'anastrozole', 'аримидекс'],
            'эксеместан': ['эксеместан', 'exemestane', 'аромазин'],
            'фулвестрант': ['фулвестрант', 'fulvestrant', 'фаслодекс'],

            'палбоциклиб': ['палбоциклиб', 'palbociclib', 'ибранс'],
            'рибоциклиб': ['рибоциклиб', 'ribociclib', 'кискали'],
            'абемациклиб': ['абемациклиб', 'abemaciclib', 'верзенио'],
            
            'этопозид': ['этопозид', 'etoposide'],
            'винбластин': ['винбластин', 'vinblastine'],
            'винкристин': ['винкристин', 'vincristine'],
            'блеомицин': ['блеомицин', 'bleomycin'],
            'пеметрексед': ['пеметрексед', 'alimta', 'pemetrexed'],
            'винорельбин': ['винорельбин', 'navelbine', 'vinorelbine'],
            'эрибулин': ['эрибулин', 'eribulin', 'халавен'],
        }
        

        self._load_protocols_from_json()
    
    def _load_protocols_from_json(self):
        """Загружает все протоколы из запаршенных JSON файлов"""
        print("\n" + "="*60)
        print("📚 ЗАГРУЗКА ПРОТОКОЛОВ ИЗ БАЗЫ МИНЗДРАВА")
        print("="*60)
        

        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_dir = os.path.join(os.path.dirname(current_dir), 'data')
        
        if not os.path.exists(json_dir):
            print(f"❌ Папка {json_dir} не найдена")
            print(f"   Создайте папку data и поместите туда JSON файлы")
            return
        
        json_files = glob(os.path.join(json_dir, '*_parsed.json'))
        print(f"🔍 Найдено JSON файлов: {len(json_files)}")
        
        if not json_files:
            print("⚠️ Нет файлов *_parsed.json в папке data")
            return
        
        loaded_count = 0
        total_protocols = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                

                filename = os.path.basename(json_file)
                cancer_type = filename.replace('_parsed.json', '')
                

                cancer_type = self._map_cancer_type(cancer_type)
                
                protocols = self._extract_protocols(data)
                
                if protocols:
                    self.protocols_db[cancer_type] = protocols
                    loaded_count += 1
                    total_protocols += len(protocols)
                    print(f"  ✅ {cancer_type:25} → {len(protocols):2} протоколов")
                    
            except Exception as e:
                print(f"  ❌ Ошибка загрузки {os.path.basename(json_file)}: {e}")
        
        print(f"\n📊 ИТОГИ ЗАГРУЗКИ:")
        print(f"   ✅ Загружено типов рака: {loaded_count}")
        print(f"   📚 Всего протоколов: {total_protocols}")
        print(f"   🎯 Доступные типы: {', '.join(self.protocols_db.keys())}")
        print("="*60)
    
    def _map_cancer_type(self, filename: str) -> str:
        """Маппит имена файлов на наши типы"""
        mapping = {
            'breast_cancer': 'breast',
            'lung_cancer': 'lung',
            'stomach_cancer': 'stomach',
            'colon_cancer': 'colon',
            'rectal_cancer': 'rectal',
            'prostate_cancer': 'prostate',
            'pancreatic_cancer': 'pancreatic',
            'esophageal_cancer': 'esophageal',
            'liver_cancer': 'liver',
            'kidney_cancer': 'kidney',
            'bladder_cancer': 'bladder',
            'ovarian_cancer': 'ovarian',
            'cervical_cancer': 'cervical',
            'uterine_cancer': 'uterine',
            'melanoma': 'melanoma',
            'thyroid_cancer': 'thyroid',
            'cancer_unknown_primary': 'cancer_unknown_primary',
            'bone_sarcoma': 'bone_sarcoma',
            'soft_tissue_sarcoma': 'soft_tissue_sarcoma',
            'gist': 'gist',
            'anal_cancer': 'anal',
            'testicular_cancer': 'testicular',
            'head_neck_cancer': 'head_neck',
            'adrenal_cancer': 'adrenal',
            'brain_metastasis': 'brain',
            'cns_tumors': 'brain',
            'kidney_parenchyma_cancer': 'kidney',
            'ovarian_borderline': 'ovarian',
            'ovarian_nonepithelial': 'ovarian',
        }
        return mapping.get(filename, filename)
    
    def _extract_protocols(self, data: dict) -> List[dict]:
        """Извлекает протоколы из JSON структуры"""
        protocols = []
        
        if 'treatment_protocols' in data:
            for p in data['treatment_protocols']:
                protocol = {
                    'name': p.get('protocol_name', ''),
                    'condition': p.get('condition', ''),
                    'stage': p.get('stage', ''),
                    'line': self._detect_line(p.get('condition', '') + ' ' + p.get('protocol_name', '')),
                    'medications': p.get('medications', []),
                    'treatment_steps': p.get('treatment_steps', []),
                    'source': 'Минздрав РФ'
                }
                if protocol['medications']:  
                    protocols.append(protocol)
        
        if 'clinical_recommendations' in data:
            recs = data['clinical_recommendations']
            if 'specific' in recs and isinstance(recs['specific'], list):
                for rec in recs['specific']:
                    if isinstance(rec, str):
                        drugs = self._extract_drugs_from_text(rec)
                        if drugs:
                            protocol = {
                                'name': 'Клиническая рекомендация',
                                'condition': rec[:100],
                                'line': self._detect_line(rec),
                                'medications': drugs,
                                'source': 'Минздрав РФ'
                            }
                            protocols.append(protocol)
        
        return protocols
    
    def _detect_line(self, text: str) -> str:
        """Определяет линию терапии из текста"""
        text_lower = text.lower()
        
        if any(x in text_lower for x in ['первая линия', 'first-line', '1st', 'первой линии']):
            return 'first_line'
        elif any(x in text_lower for x in ['вторая линия', 'second-line', '2nd', 'второй линии']):
            return 'second_line'
        elif any(x in text_lower for x in ['третья линия', 'third-line', '3rd', 'третьей линии']):
            return 'third_line'
        elif any(x in text_lower for x in ['адъювант', 'adjuvant']):
            return 'adjuvant'
        elif any(x in text_lower for x in ['неоадъювант', 'neoadjuvant']):
            return 'neoadjuvant'
        elif any(x in text_lower for x in ['метастатич', 'metastatic']):
            return 'metastatic'
        else:
            return 'unknown'
    
    def _extract_drugs_from_text(self, text: str) -> List[str]:
        """Извлекает препараты из текста"""
        known_drugs = [
            'паклитаксел', 'карбоплатин', 'цисплатин', 'гемцитабин',
            'трастузумаб', 'трастузумаб дерукстекан', 'пертузумаб', 'тукатиниб',
            'осимертиниб', 'гефитиниб', 'эрлотиниб', 'алектиниб',
            'пембролизумаб', 'ниволумаб', 'атезолизумаб', 'бевацизумаб',
            'рамуцирумаб', 'иринотекан', 'доцетаксел', 'капецитабин',
            'оксалиплатин', 'фторурацил', 'этопозид', 'доксорубицин',
            'циклофосфамид', 'метотрексат', 'винорельбин', 'эрибулин'
        ]
        
        found = []
        text_lower = text.lower()
        for drug in known_drugs:
            if drug in text_lower:
                found.append(drug)
        
        return found
    
    def _is_drug_match(self, prescribed: str, protocol_drug: str) -> Tuple[bool, str]:
        """
        Проверяет, соответствует ли назначенный препарат препарату из протокола
        с учетом синонимов и семейств
        """
        prescribed_lower = prescribed.lower()
        protocol_lower = protocol_drug.lower()
        

        if protocol_lower in prescribed_lower or prescribed_lower in protocol_lower:
            return True, 'exact'
        

        for family, members in self.drug_families.items():
            protocol_in_family = any(member in protocol_lower for member in members)
            prescribed_in_family = any(member in prescribed_lower for member in members)
            
            if prescribed_in_family and protocol_in_family:
                return True, 'family'
        
        return False, 'none'
    
    def calculate_score_from_protocols(self,
                                      cancer_type: str,
                                      treatment_lines: Dict[str, Any],
                                      biomarkers: Dict[str, bool]) -> Dict[str, Any]:
        """
        Расчет score на основе протоколов из базы Минздрава
        """

        protocols = self.protocols_db.get(cancer_type, [])
        
        if not protocols:

            print(f"🤖 Нет протоколов в базе для {cancer_type}, использую AI-оценку")
            return self._calculate_with_ai(cancer_type, treatment_lines, biomarkers)
        
        print(f"\n🏥 АНАЛИЗ ПО БАЗЕ МИНЗДРАВА ({cancer_type})")
        print(f"   Найдено протоколов: {len(protocols)}")
        
        lines = treatment_lines.get('lines', [])
        findings = []
        total_score = 0
        max_possible = 0
        lines_analyzed = 0
        source_type = 'minzdrav_db'
        

        for line_data in lines:
            line_num = line_data.get('line', 1)
            treatments = line_data.get('treatments', [])
            response = line_data.get('response', '')
            
            if not treatments:
                continue
            
            lines_analyzed += 1
            

            matching_protocol = self._find_matching_protocol(
                protocols, line_num, treatments, biomarkers
            )
            
            if matching_protocol:

                line_result = self._evaluate_against_protocol(
                    treatments, matching_protocol, line_num
                )
                protocol_used = matching_protocol.get('name', 'Неизвестный протокол')
                print(f"   Линия {line_num}: найден протокол '{protocol_used}'")
            else:

                print(f"   Линия {line_num}: нет подходящего протокола, использую AI")
                line_result = self._evaluate_line_with_ai(
                    cancer_type, treatments, biomarkers, line_num
                )
                source_type = 'mixed' 
            

            for f in line_result.get('findings', []):
                f['line'] = line_num
                f['line_response'] = response
                findings.append(f)
            
            line_score = line_result.get('score', 0)
            line_max = line_result.get('max_score', len(treatments) * self.max_score_per_treatment)
            

            line_weight = self._get_line_weight(line_num)
            weighted_score = line_score * line_weight
            
            total_score += weighted_score
            max_possible += line_max * line_weight
            
            print(f"      → Оценка: {weighted_score:.1f}/{line_max} (вес: {line_weight})")
        

        planned = treatment_lines.get('planned')
        if planned and planned.get('treatments'):
            planned_treatments = planned.get('treatments', [])
            print(f"\n🔮 Планируемое лечение: {planned_treatments}")
            

            matching_protocol = self._find_matching_protocol(
                protocols, 99, planned_treatments, biomarkers  
            )
            
            if matching_protocol:
                planned_result = self._evaluate_against_protocol(
                    planned_treatments, matching_protocol, 99
                )
            else:
                planned_result = self._evaluate_line_with_ai(
                    cancer_type, planned_treatments, biomarkers, 99
                )
                source_type = 'mixed'
            
            for f in planned_result.get('findings', []):
                f['line'] = 'planned'
                f['is_planned'] = True
                findings.append(f)
            
            planned_score = planned_result.get('score', 0)
            planned_max = planned_result.get('max_score', len(planned_treatments) * self.max_score_per_treatment)
            
            total_score += planned_score * self.line_weights['planned']
            max_possible += planned_max * self.line_weights['planned']
            
            print(f"      → Оценка планируемого: {planned_score * self.line_weights['planned']:.1f}/{planned_max}")
        

        if max_possible > 0:
            final_score = int((total_score / max_possible) * 100)
        else:
            final_score = 0
        
        message = self._get_score_message(final_score, cancer_type, len(protocols))
        
        print(f"\n📊 ИТОГОВЫЙ SCORE: {final_score}%")
        print(f"📌 Источник: {source_type}")
        
        return {
            'score': final_score,
            'findings': findings,
            'source': source_type,
            'message': message,
            'analyzed_lines': lines_analyzed,
            'protocols_available': len(protocols)
        }
    
    def _find_matching_protocol(self, protocols: List[dict], line_num: int, 
                           treatments: List[str], biomarkers: dict) -> Optional[dict]:
        """Ищет протокол с учетом штрафов за критические ошибки"""
        
        scored_protocols = []
        
        for protocol in protocols:
            score = 0
            protocol_meds = protocol.get('medications', [])
            protocol_line = protocol.get('line', 'unknown')
            
            if not protocol_meds:
                continue
            

            critical_errors = 0
            for t in treatments:
                t_lower = t.lower()

                if biomarkers.get('her2_negative') and any(x in t_lower for x in ['трастузумаб', 'пертузумаб', 'тукатиниб']):
                    critical_errors += 100 
                if 'тамоксифен' in t_lower or 'летрозол' in t_lower:
                    critical_errors += 100
            
            score -= critical_errors
            

            matches = 0
            for t in treatments:
                for pm in protocol_meds:
                    is_match, _ = self._is_drug_match(t, pm)
                    if is_match:
                        matches += 1
                        break
            
            if matches > 0:
                score += matches * 10
            
            if line_num == 1 and protocol_line in ['first_line', 'adjuvant', 'neoadjuvant']:
                score += 30
            elif line_num == 2 and protocol_line in ['second_line', 'metastatic']:
                score += 30
            elif line_num >= 3 and protocol_line in ['third_line', 'metastatic']:
                score += 30
            
            if score > 0 or critical_errors > 0:
                scored_protocols.append((score, protocol))
        
        if scored_protocols:
            scored_protocols.sort(reverse=True, key=lambda x: x[0])
            return scored_protocols[0][1]
        
        return None
    
    def _evaluate_against_protocol(self, treatments: List[str], 
                                   protocol: dict, line_num: int) -> dict:
        """Оценивает соответствие лечения протоколу"""
        findings = []
        score = 0
        max_score = len(treatments) * self.max_score_per_treatment
        
        protocol_meds = protocol.get('medications', [])
        protocol_name = protocol.get('name', 'Неизвестный протокол')
        
        for treatment in treatments:
            matched = False
            match_type = 'none'
            
            for pm in protocol_meds:
                is_match, mtype = self._is_drug_match(treatment, pm)
                if is_match:
                    matched = True
                    match_type = mtype
                    break
            
            if matched:
                if match_type == 'exact':
                    points = self.max_score_per_treatment
                    status = 'correct'
                    comment = f'✅ Полное соответствие протоколу: {protocol_name}'
                else:
                    points = int(self.max_score_per_treatment * 0.9)
                    status = 'correct'
                    comment = f'✅ Родственный препарат, соответствует протоколу: {protocol_name}'
                
                findings.append({
                    'treatment': treatment,
                    'status': status,
                    'comment': comment,
                    'score_contributed': points,
                    'protocol': protocol_name
                })
                score += points
            else:
                findings.append({
                    'treatment': treatment,
                    'status': 'warning',
                    'comment': f'⚠️ Не входит в протокол {protocol_name}',
                    'score_contributed': 5, 
                    'protocol': protocol_name
                })
                score += 5
        
        return {
            'score': score,
            'max_score': max_score,
            'findings': findings,
            'protocol_used': protocol_name
        }
    
    def _evaluate_line_with_ai(self, cancer_type: str, treatments: List[str],
                           biomarkers: dict, line_num: int) -> dict:
        """Оценивает линию с помощью AI - СТРОГАЯ ВЕРСИЯ"""
        from ai_service import ai_service
        
        findings = []
        score = 0
        max_score = len(treatments) * self.max_score_per_treatment
        
        for treatment in treatments:
            ai_opinion = ai_service.ask_about_treatment(
                cancer_type=cancer_type,
                treatment=treatment,
                biomarkers=biomarkers
            )
            
            confidence = ai_opinion.get('confidence', 0.5)
            

            ai_score = ai_opinion.get('score_recommendation', None)
            
            if ai_opinion.get('is_contraindicated', False):
                points = 0
                status = 'critical'
                comment = f'❌ ПРОТИВОПОКАЗАН: {ai_opinion.get("explanation", "")}'
                print(f"      ❌ {treatment}: ПРОТИВОПОКАЗАН")
                
            elif ai_opinion.get('is_appropriate', False):
                if ai_score is not None:
                    points = ai_score
                elif confidence >= 0.9:
                    points = self.max_score_per_treatment
                elif confidence >= 0.7:
                    points = int(self.max_score_per_treatment * 0.9)
                else:
                    points = int(self.max_score_per_treatment * 0.8)
                
                status = 'correct'
                comment = f'✅ {ai_opinion.get("explanation", "Подходит")}'
                print(f"      ✅ {treatment}: ПОДХОДИТ ({points} pts)")
                
            else:
                if ai_score is not None:
                    points = ai_score
                else:
                    points = int(self.max_score_per_treatment * 0.3) 
                
                status = 'warning'
                comment = f'⚠️ {ai_opinion.get("explanation", "Нестандартное назначение")}'
                print(f"      ⚠️ {treatment}: НЕСТАНДАРТНО ({points} pts)")
            
            findings.append({
                'treatment': treatment,
                'status': status,
                'comment': comment,
                'score_contributed': points,
                'source': 'ai',
                'ai_confidence': confidence
            })
            
            score += points
        
        return {
            'score': score,
            'max_score': max_score,
            'findings': findings,
            'source': 'ai'
        }
    
    def _calculate_with_ai(self, cancer_type: str, treatment_lines: Dict,
                          biomarkers: dict) -> Dict:
        """Полностью AI-оценка если нет в базе"""
        lines = treatment_lines.get('lines', [])
        findings = []
        total_score = 0
        max_possible = 0
        
        print(f"\n🤖 ПОЛНАЯ AI-ОЦЕНКА для {cancer_type}")
        
        for line_data in lines:
            line_num = line_data.get('line', 1)
            treatments = line_data.get('treatments', [])
            
            if not treatments:
                continue
            
            line_result = self._evaluate_line_with_ai(
                cancer_type, treatments, biomarkers, line_num
            )
            
            for f in line_result.get('findings', []):
                f['line'] = line_num
                findings.append(f)
            
            line_weight = self._get_line_weight(line_num)
            total_score += line_result['score'] * line_weight
            max_possible += line_result['max_score'] * line_weight
        

        planned = treatment_lines.get('planned')
        if planned and planned.get('treatments'):
            planned_treatments = planned.get('treatments', [])
            planned_result = self._evaluate_line_with_ai(
                cancer_type, planned_treatments, biomarkers, 99
            )
            
            for f in planned_result.get('findings', []):
                f['line'] = 'planned'
                f['is_planned'] = True
                findings.append(f)
            
            total_score += planned_result['score'] * self.line_weights['planned']
            max_possible += planned_result['max_score'] * self.line_weights['planned']
        
        final_score = int((total_score / max_possible) * 100) if max_possible > 0 else 50
        
        return {
            'score': final_score,
            'findings': findings,
            'source': 'ai_only',
            'message': f"🤖 Оценка на основе AI (нет данных в базе Минздрава для {cancer_type})",
            'analyzed_lines': len(lines)
        }
    
    def _get_line_weight(self, line_num: int) -> float:
        """Возвращает вес для линии терапии"""
        if line_num == 1:
            return self.line_weights['first_line']
        elif line_num == 2:
            return self.line_weights['second_line']
        elif line_num == 3:
            return self.line_weights['third_line']
        elif line_num >= 4:
            return self.line_weights['fourth_plus']
        elif line_num == 99: 
            return self.line_weights['planned']
        else:
            return 0.8
    
    def _get_score_message(self, score: int, cancer_type: str, protocols_count: int) -> str:
        """Возвращает сообщение в зависимости от score"""
        if score >= 90:
            return f"✅ Отличное соответствие протоколам Минздрава для {cancer_type} (доступно {protocols_count} протоколов)"
        elif score >= 75:
            return f"👍 Хорошее соответствие, незначительные отклонения от протоколов ({protocols_count} протоколов)"
        elif score >= 60:
            return f"⚠️ Частичное соответствие, требуется анализ отклонений ({protocols_count} протоколов)"
        elif score >= 40:
            return f"❌ Значительные отклонения от протоколов Минздрава ({protocols_count} протоколов)"
        else:
            return f"🚨 Критическое несоответствие протоколам! Требуется консилиум ({protocols_count} протоколов)"
    

    def calculate_score(self, cancer_type: str, prescribed_treatments: List[str],
                        biomarkers: Dict[str, bool], use_ai_fallback: bool = True) -> Dict[str, Any]:
        """Старый метод для обратной совместимости"""

        treatment_lines = {
            'lines': [
                {
                    'line': 1,
                    'treatments': prescribed_treatments,
                    'response': 'неизвестно'
                }
            ]
        }
        return self.calculate_score_from_protocols(cancer_type, treatment_lines, biomarkers)



print("\n🔧 Создание глобального экземпляра scorer...")
try:
    scorer = ComplianceScorer()
    print(f"✅ Глобальный экземпляр 'scorer' успешно создан")
    print(f"📊 Загружено протоколов: {len(scorer.protocols_db)}")
    print(f"🎯 Доступные типы: {list(scorer.protocols_db.keys())}")
except Exception as e:
    print(f"❌ Ошибка создания scorer: {e}")

    class DummyScorer:
        def calculate_score(self, *args, **kwargs):
            return {'score': 50, 'message': 'Scorer unavailable', 'findings': []}
        def calculate_score_from_protocols(self, *args, **kwargs):
            return {'score': 50, 'message': 'Scorer unavailable', 'findings': []}
    
    scorer = DummyScorer()
    print("⚠️ Используется dummy scorer (только для аварийного режима)")

__all__ = ['ComplianceScorer', 'scorer']

print("="*60 + "\n")