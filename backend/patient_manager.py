

import uuid
from datetime import datetime
import json
import os

class PatientManager:
    def __init__(self, db_file="patients_db.json"):
        self.db_file = db_file
        self.patients = {}
        self.load_patients()
        print(f"📁 Загружено пациентов: {len(self.patients)}")

    def load_patients(self):
        """Загружает пациентов из файла"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.patients = json.load(f)
                print(f"✅ Пациенты загружены из {self.db_file}")
            except Exception as e:
                print(f"❌ Ошибка загрузки пациентов: {e}")
                self.patients = {}
        else:
            self.patients = {}

    def _save_patients(self):
        """Сохраняет пациентов в файл"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.patients, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения пациентов: {e}")
            return False

    def create_patient(self, initials="", age=0, gender=""):
        """Создает нового пациента"""
        patient_id = f"patient-{uuid.uuid4().hex[:8]}"
        
        self.patients[patient_id] = {
            "id": patient_id,
            "initials": initials,
            "age": age,
            "gender": gender,
            "diagnosis": "",
            "created_at": datetime.now().isoformat(),
            "last_visit": "",
            "history": [],
            "timeline": []
        }
        
        self._save_patients()
        print(f"✅ Создан пациент {patient_id}")
        return patient_id

    def create_patient_with_id(self, patient_id):
        """Создает пациента с указанным ID"""
        if patient_id not in self.patients:
            self.patients[patient_id] = {
                "id": patient_id,
                "initials": "",
                "age": 0,
                "gender": "",
                "diagnosis": "",
                "created_at": datetime.now().isoformat(),
                "last_visit": "",
                "history": [],
                "timeline": []
            }
            self._save_patients()
            print(f"✅ Создан пациент с ID {patient_id}")
        
        return patient_id

    def get_patient(self, patient_id):
        """Возвращает данные пациента"""
        return self.patients.get(patient_id)

    def get_all_patients(self):
        """Возвращает список всех пациентов"""
        patients_list = []
        for patient_id, data in self.patients.items():
            patients_list.append({
                "id": patient_id,
                "initials": data.get("initials", ""),
                "age": data.get("age", 0),
                "gender": data.get("gender", ""),
                "diagnosis": data.get("diagnosis", ""),
                "last_visit": data.get("last_visit", ""),
                "created_at": data.get("created_at", ""),
                "history_count": len(data.get("history", []))
            })
        

        patients_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return patients_list

    def search_patients(self, query):
        """Поиск пациентов"""
        results = []
        query = query.lower()
        
        for patient_id, data in self.patients.items():
            if (query in patient_id.lower() or 
                query in data.get("initials", "").lower() or
                query in data.get("diagnosis", "").lower()):
                results.append({
                    "id": patient_id,
                    "initials": data.get("initials", ""),
                    "age": data.get("age", 0),
                    "gender": data.get("gender", ""),
                    "diagnosis": data.get("diagnosis", "")
                })
        
        return results

    def add_history_entry(self, patient_id, history_text, analysis_result):
        """Добавляет запись в историю пациента"""
        try:
            patient = self.get_patient(patient_id)
            if not patient:
                print(f"❌ Пациент {patient_id} не найден")
                return False
            

            entry_id = str(uuid.uuid4())
            

            doctor_version = analysis_result.get('doctor_version', {})
            patient_version = analysis_result.get('patient_version', {})
            

            diagnosis = doctor_version.get('diagnosis', {}).get('extracted', '')
            if not diagnosis:
                diagnosis = analysis_result.get('cancer_type', 'Диагноз не указан')
            

            entry = {
                "id": entry_id,
                "timestamp": datetime.now().isoformat(),
                "history": history_text[:200] + "..." if len(history_text) > 200 else history_text,
                "diagnosis": diagnosis,
                "compliance_score": doctor_version.get('compliance_score', 0),
                "status": patient_version.get('status', '📋'),
                "full_result": analysis_result
            }
            
            print(f"➕ Создана запись с ID: {entry_id}")
            print(f"   Диагноз: {entry['diagnosis']}")
            print(f"   Score: {entry['compliance_score']}")
            

            if "history" not in patient:
                patient["history"] = []
            
            patient["history"].append(entry)
            patient["last_visit"] = datetime.now().isoformat()
            

            self._save_patients()
            
            print(f"✅ Запись добавлена. Всего записей: {len(patient['history'])}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении записи: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_patient_history(self, patient_id, limit=20):
        """Возвращает историю проверок пациента"""
        patient = self.get_patient(patient_id)
        if not patient:
            return []
        
        history = patient.get("history", [])

        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        

        if len(history) > limit:
            history = history[:limit]
        
        return history

    def delete_history_entry(self, patient_id, entry_id):
        """Удаляет конкретную запись из истории"""
        try:
            patient = self.get_patient(patient_id)
            if not patient:
                return False, "Пациент не найден"
            
            original_length = len(patient.get("history", []))
            patient["history"] = [h for h in patient.get("history", []) if h.get("id") != entry_id]
            new_length = len(patient.get("history", []))
            
            if original_length == new_length:
                return False, "Запись не найдена"
            
            self._save_patients()
            return True, f"Удалено записей: {original_length - new_length}"
            
        except Exception as e:
            return False, str(e)

    def clear_patient_history(self, patient_id):
        """Очищает всю историю пациента"""
        try:
            patient = self.get_patient(patient_id)
            if not patient:
                return False, "Пациент не найден"
            
            old_count = len(patient.get("history", []))
            patient["history"] = []
            patient["timeline"] = []
            
            self._save_patients()
            return True, f"Очищено записей: {old_count}"
            
        except Exception as e:
            return False, str(e)


patient_manager = PatientManager()