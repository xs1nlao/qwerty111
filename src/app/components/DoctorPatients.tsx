import { motion, AnimatePresence } from "motion/react";
import { 
  Users, User, Plus, Calendar, Activity, ChevronRight, 
  Shield, Clock, X, CheckCircle, Search, Filter,
  FileText, AlertCircle, TrendingUp, CalendarClock,
  History, BarChart3, MoreVertical, Trash2, AlertTriangle,
  RefreshCw
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";

interface Patient {
  id: string;
  initials: string;
  age: number;
  gender: string;
  diagnosis: string;
  last_visit: string;
  history_count: number;
  created_at: string;
}

interface DoctorPatientsProps {
  onSelectPatient: (patientId: string | null) => void;
  selectedPatientId: string | null;
}

export function DoctorPatients({ onSelectPatient, selectedPatientId }: DoctorPatientsProps) {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [newPatient, setNewPatient] = useState({
    initials: '',
    age: '',
    gender: 'ж',
    diagnosis: ''
  });

  const loadPatients = useCallback(async (showLoadingIndicator = true) => {
    if (showLoadingIndicator) setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/patients');
      const data = await response.json();
     
      setPatients(data.patients || []);
      console.log(`📋 Загружено ${data.patients?.length || 0} пациентов`);
    } catch (error) {
      console.error("Ошибка загрузки пациентов:", error);
    } finally {
      if (showLoadingIndicator) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  useEffect(() => {
    const handlePatientUpdate = () => {
      console.log("🔄 Получено событие обновления пациентов");
      loadPatients(false); 
    };

    window.addEventListener('patient-updated', handlePatientUpdate);
    window.addEventListener('patient-history-updated', handlePatientUpdate);
    
    return () => {
      window.removeEventListener('patient-updated', handlePatientUpdate);
      window.removeEventListener('patient-history-updated', handlePatientUpdate);
    };
  }, [loadPatients]);

  const handleAddPatient = async () => {
    if (!newPatient.initials || !newPatient.age) {
      alert("Заполните инициалы и возраст");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/patients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initials: newPatient.initials,
          age: parseInt(newPatient.age),
          gender: newPatient.gender
        })
      });

      const data = await response.json();
      
      if (data.success) {
        await loadPatients(true);
        
      
        setShowAddForm(false);
        setNewPatient({ initials: '', age: '', gender: 'ж', diagnosis: '' });
  
        onSelectPatient(data.patient_id);
        
    
        window.dispatchEvent(new CustomEvent('patient-updated'));
      }
    } catch (error) {
      console.error("Ошибка создания пациента:", error);
      alert('Ошибка при создании пациента');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePatient = async (patientId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/patient/${patientId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        if (selectedPatientId === patientId) {
          onSelectPatient(null);
        }
        
     
        await loadPatients(true);
        setShowDeleteConfirm(null);
        
      
        window.dispatchEvent(new CustomEvent('patient-updated'));
      } else {
        alert('Ошибка при удалении пациента');
      }
    } catch (error) {
      console.error("Ошибка удаления пациента:", error);
      alert('Ошибка при удалении пациента');
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter(p => 
    p.initials.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.diagnosis.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading && patients.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      {/* Заголовок */}
      <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-teal-50 to-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users size={20} className="text-teal-600" />
            <h2 className="font-bold text-lg">Мои пациенты</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadPatients(true)}
              className="p-2 hover:bg-teal-200 rounded-lg transition-colors"
              title="Обновить список"
              disabled={loading}
            >
              <RefreshCw size={16} className={`text-teal-600 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setShowAddForm(true)}
              className="p-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors shadow-sm flex items-center gap-1"
              disabled={loading}
            >
              <Plus size={18} />
              <span className="text-sm">Новый</span>
            </button>
          </div>
        </div>

        {/* Поиск */}
        <div className="mt-3 relative">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Поиск по имени, диагнозу или ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
          />
        </div>

        {/* Индикатор количества */}
        <div className="mt-2 text-xs text-slate-500">
          Найдено: {filteredPatients.length} из {patients.length}
        </div>
      </div>

      {/* Форма добавления */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-teal-200 bg-teal-50"
          >
            <div className="p-4 space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="font-medium text-teal-800">Новый пациент</h3>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="p-1 hover:bg-teal-200 rounded"
                >
                  <X size={16} />
                </button>
              </div>
              
              <input
                type="text"
                placeholder="Инициалы (например, И.П.) *"
                value={newPatient.initials}
                onChange={(e) => setNewPatient({...newPatient, initials: e.target.value})}
                className="w-full p-2 text-sm border border-teal-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
              />
              
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Возраст *"
                  value={newPatient.age}
                  onChange={(e) => setNewPatient({...newPatient, age: e.target.value})}
                  className="w-full p-2 text-sm border border-teal-200 rounded-lg"
                />
                <select
                  value={newPatient.gender}
                  onChange={(e) => setNewPatient({...newPatient, gender: e.target.value})}
                  className="w-full p-2 text-sm border border-teal-200 rounded-lg"
                >
                  <option value="ж">Женский</option>
                  <option value="м">Мужской</option>
                </select>
              </div>

              <input
                type="text"
                placeholder="Предварительный диагноз (необязательно)"
                value={newPatient.diagnosis}
                onChange={(e) => setNewPatient({...newPatient, diagnosis: e.target.value})}
                className="w-full p-2 text-sm border border-teal-200 rounded-lg"
              />

              <button
                onClick={handleAddPatient}
                disabled={loading}
                className="w-full p-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:bg-teal-300 disabled:cursor-not-allowed"
              >
                {loading ? 'Создание...' : 'Создать карту пациента'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Список пациентов */}
      <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
        {filteredPatients.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Users size={24} className="text-slate-300" />
            </div>
            <p className="text-sm mb-2">
              {searchQuery ? 'Ничего не найдено' : 'Нет пациентов'}
            </p>
            <p className="text-xs">
              {searchQuery 
                ? 'Попробуйте изменить поиск'
                : 'Нажмите "Новый" чтобы добавить пациента'}
            </p>
          </div>
        ) : (
          filteredPatients.map((patient) => (
            <motion.div
              key={patient.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              layoutId={patient.id}
              className="border-l-2 border-transparent hover:border-teal-500 transition-all relative"
            >
              {/* Диалог подтверждения удаления */}
              <AnimatePresence>
                {showDeleteConfirm === patient.id && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute inset-0 bg-white/95 backdrop-blur-sm z-10 flex items-center justify-center p-4 rounded-lg"
                  >
                    <div className="text-center">
                      <AlertTriangle size={32} className="text-red-500 mx-auto mb-2" />
                      <p className="text-sm font-medium mb-1">Удалить пациента?</p>
                      <p className="text-xs text-slate-500 mb-3">
                        {patient.initials}, {patient.age} лет<br/>
                        История: {patient.history_count} записей
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDeletePatient(patient.id)}
                          disabled={loading}
                          className="flex-1 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-red-300"
                        >
                          Удалить
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(null)}
                          className="flex-1 px-3 py-1.5 bg-slate-200 text-slate-700 text-sm rounded-lg hover:bg-slate-300"
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Карточка пациента */}
              <div
                onClick={() => onSelectPatient(patient.id)}
                className={`p-4 cursor-pointer transition-all ${
                  selectedPatientId === patient.id 
                    ? 'bg-teal-50 border-b-2 border-teal-500' 
                    : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Аватар */}
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shrink-0 ${
                    selectedPatientId === patient.id
                      ? 'bg-teal-600'
                      : 'bg-gradient-to-br from-teal-400 to-teal-600'
                  }`}>
                    {patient.initials || patient.id.slice(-2).toUpperCase()}
                  </div>

                  {/* Информация */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium truncate">
                        {patient.initials || 'Без имени'}
                      </h3>
                      <div className="flex items-center gap-1">
                        {selectedPatientId === patient.id ? (
                          <CheckCircle size={16} className="text-teal-600" />
                        ) : (
                          <ChevronRight size={16} className="text-slate-400" />
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-2 flex-wrap">
                      <span className="bg-slate-100 px-2 py-0.5 rounded-full">
                        {patient.age} лет
                      </span>
                      <span className="bg-slate-100 px-2 py-0.5 rounded-full">
                        {patient.gender === 'ж' ? '♀' : '♂'}
                      </span>
                      <span className="bg-slate-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Activity size={10} />
                        {patient.history_count} записей
                      </span>
                    </div>

                    {/* Диагноз */}
                    {patient.diagnosis && (
                      <div className="text-sm text-slate-700 mb-2 line-clamp-1">
                        {patient.diagnosis}
                      </div>
                    )}

                    {/* Последний визит и кнопки */}
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1 text-slate-400">
                        <Calendar size={12} />
                        {patient.last_visit ? new Date(patient.last_visit).toLocaleString('ru-RU', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        }) : 'Нет визитов'}
                      </span>
                      
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                          }}
                          className="p-1 hover:bg-teal-100 rounded transition-colors"
                          title="Просмотр истории"
                        >
                          <History size={14} className="text-slate-500" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowDeleteConfirm(patient.id);
                          }}
                          className="p-1 hover:bg-red-100 rounded transition-colors"
                          title="Удалить пациента"
                        >
                          <Trash2 size={14} className="text-red-400 hover:text-red-600" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Статистика */}
      {patients.length > 0 && (
        <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex items-center justify-between">
          <span>Всего: {patients.length}</span>
          <span>Активных: {patients.filter(p => p.history_count > 0).length}</span>
          <span>Последнее обновление: {new Date().toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  );
}