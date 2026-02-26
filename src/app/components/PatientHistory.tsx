import { motion, AnimatePresence } from "motion/react";
import { 
  Calendar, Clock, Activity, ChevronRight, Shield, 
  TrendingUp, TrendingDown, Minus, FileText, AlertCircle,
  CheckCircle, XCircle, History, User, Copy, Check,
  Trash2, AlertTriangle, RefreshCw
} from "lucide-react";
import { useState, useEffect } from "react";

interface HistoryEntry {
  id: string;
  timestamp: string;
  date: string;
  diagnosis: string;
  compliance_score: number;
  status: string;
  full_result?: any;
}

interface PatientHistoryProps {
  patientId: string;
  onSelectEntry: (entry: HistoryEntry) => void;
  userType: "doctor" | "patient";
  showId?: boolean;
  onDeleteEntry?: (entryId: string) => void;
  onClearHistory?: () => void;
}

export function PatientHistory({ 
  patientId, 
  onSelectEntry, 
  userType, 
  showId = false,
  onDeleteEntry,
  onClearHistory
}: PatientHistoryProps) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async (showLoading = true) => {
    if (!patientId) return;
    
    if (showLoading) setLoading(true);
    setError(null);
    
    try {
      console.log(`📋 Загрузка истории для пациента ${patientId}...`);
      const response = await fetch(`http://localhost:5000/api/patient/${patientId}/history`);
      const data = await response.json();
      
      console.log("📥 Получены данные истории:", data);
      
      const processedHistory = (data.history || []).map((entry: any, index: number) => {
        const entryId = entry.id || `entry-${Date.now()}-${index}-${Math.random()}`;
        console.log(`📝 Запись ${index}: id=${entryId}, timestamp=${entry.timestamp}`);
        
        return {
          ...entry,
          id: entryId,
          date: entry.timestamp ? new Date(entry.timestamp).toLocaleString('ru-RU') : 'Дата неизвестна'
        };
      });
      
      console.log(`✅ Загружено ${processedHistory.length} записей с ID:`, 
        processedHistory.map(e => ({ id: e.id, date: e.date })));
      
      setHistory(processedHistory);
    } catch (error) {
      console.error("❌ Ошибка загрузки истории:", error);
      setError('Ошибка загрузки истории');
    } finally {
      if (showLoading) setLoading(false);
    }
  };
  useEffect(() => {
    if (patientId) {
      loadHistory();
    }
    
    const handleHistoryUpdate = () => {
      console.log("🔄 Получено событие обновления истории");
      loadHistory(false);
    };
    window.addEventListener('patient-history-updated', handleHistoryUpdate)
    return () => {
      window.removeEventListener('patient-history-updated', handleHistoryUpdate);
    };
  }, [patientId]);
  const handleDeleteEntry = async (entryId: string) => {
    if (deleting) return;
    
    setDeleting(entryId);
    setError(null);
    
    try {
      console.log(`🗑️ Удаление записи ${entryId}...`);
      if (onDeleteEntry) {
        await onDeleteEntry(entryId);
      } else {
        const response = await fetch(`http://localhost:5000/api/patient/${patientId}/history/${entryId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error('Ошибка при удалении');
        }
        
        const data = await response.json();
        console.log("✅ Ответ сервера:", data);
      }
      
      setHistory(prev => prev.filter(entry => entry.id !== entryId));
      window.dispatchEvent(new CustomEvent('patient-history-updated'));
    
      setDeleteConfirm(null);
      
    } catch (error) {
      console.error("❌ Ошибка удаления записи:", error);
      setError('Не удалось удалить запись');
    } finally {
      setDeleting(null);
    }
  };

  const handleClearAll = async () => {
    if (clearing) return;
    
    setClearing(true);
    setError(null);
    
    try {
      console.log(`🧹 Очистка всей истории пациента ${patientId}...`);
    
      if (onClearHistory) {
        await onClearHistory();
      } else {

        const response = await fetch(`http://localhost:5000/api/patient/${patientId}/history/clear`, {
          method: 'POST'
        });
        
        if (!response.ok) {
          throw new Error('Ошибка при очистке');
        }
        
        const data = await response.json();
        console.log("✅ Ответ сервера:", data);
      }
      
      setHistory([]);
      
      window.dispatchEvent(new CustomEvent('patient-history-updated'));
      
     
      setShowDeleteAllConfirm(false);
      
    } catch (error) {
      console.error("❌ Ошибка очистки истории:", error);
      setError('Не удалось очистить историю');
    } finally {
      setClearing(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(patientId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 70) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

 
  const getStatusIcon = (status: string) => {
    if (status?.includes('✅')) return '✅';
    if (status?.includes('⚠️')) return '⚠️';
    if (status?.includes('❌')) return '❌';
    return '📋';
  };

  if (loading && history.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <div className="flex flex-col items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mb-3"></div>
          <p className="text-sm text-slate-500">Загрузка истории...</p>
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
            <History size={20} className="text-teal-600" />
            <h2 className="font-bold text-lg">
              {userType === "doctor" ? "История проверок пациента" : "Моя история"}
            </h2>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Кнопка обновления */}
            <button
              onClick={() => loadHistory(true)}
              className="p-2 hover:bg-white rounded-lg transition-colors"
              title="Обновить"
              disabled={loading}
            >
              <RefreshCw size={16} className={`text-teal-600 ${loading ? 'animate-spin' : ''}`} />
            </button>
            
            {/* Кнопка очистки для пациента */}
            {userType === "patient" && history.length > 0 && (
              <button
                onClick={() => setShowDeleteAllConfirm(true)}
                className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                title="Очистить всю историю"
                disabled={clearing}
              >
                <Trash2 size={16} className="text-red-500" />
              </button>
            )}
            
            <span className="text-xs bg-white px-2 py-1 rounded-full text-slate-600">
              {history.length} {history.length === 1 ? 'запись' : 
                history.length < 5 ? 'записи' : 'записей'}
            </span>
          </div>
        </div>

        {/* ID пациента */}
        {(showId || userType === "patient") && (
          <div className="mt-2 flex items-center gap-2 text-sm">
            <span className="text-slate-500">Ваш ID:</span>
            <code className="bg-white px-2 py-1 rounded border border-slate-200 text-teal-600 font-mono text-xs">
              {patientId}
            </code>
            <button
              onClick={copyToClipboard}
              className="p-1 hover:bg-white rounded transition-colors"
              title="Копировать ID"
            >
              {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} className="text-slate-400" />}
            </button>
          </div>
        )}

        {/* Ошибка */}
        {error && (
          <div className="mt-2 p-2 bg-red-50 rounded-lg flex items-center gap-2 text-xs text-red-600">
            <AlertTriangle size={14} />
            {error}
          </div>
        )}
      </div>

      {/* Диалог подтверждения удаления всех записей */}
      <AnimatePresence>
        {showDeleteAllConfirm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-4 bg-red-50 border-b border-red-200"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle size={20} className="text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 mb-2">
                  Очистить всю историю?
                </p>
                <p className="text-xs text-red-600 mb-3">
                  Будет удалено {history.length} записей. Это действие нельзя отменить.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleClearAll}
                    disabled={clearing}
                    className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {clearing ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        Очистка...
                      </>
                    ) : (
                      'Очистить'
                    )}
                  </button>
                  <button
                    onClick={() => setShowDeleteAllConfirm(false)}
                    className="px-3 py-1.5 bg-white text-slate-600 text-sm rounded-lg hover:bg-slate-100"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Список истории */}
      {history.length === 0 ? (
        <div className="p-8 text-center text-slate-400">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <History size={24} className="text-slate-300" />
          </div>
          <p className="text-sm mb-2">Нет проверок</p>
          <p className="text-xs">
            {userType === "patient" 
              ? "Ваши проверки будут появляться здесь"
              : "У этого пациента пока нет проверок"}
          </p>
        </div>
      ) : (
        <div className="divide-y divide-slate-100 max-h-[400px] overflow-y-auto">
          {history.slice().reverse().map((entry) => (
            <div
              key={entry.id}
              className="relative group hover:bg-slate-50 transition-colors"
            >
              {/* Кнопка удаления для пациента*/}
              {userType === "patient" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteConfirm(entry.id);
                  }}
                  disabled={deleting === entry.id}
                  className="absolute right-2 top-2 p-1.5 bg-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity shadow-sm hover:bg-red-50 disabled:opacity-50 z-10"
                  title="Удалить запись"
                >
                  {deleting === entry.id ? (
                    <RefreshCw size={14} className="animate-spin text-red-500" />
                  ) : (
                    <Trash2 size={14} className="text-red-500" />
                  )}
                </button>
              )}

              {/* Диалог подтверждения удаления записи */}
              <AnimatePresence>
                {deleteConfirm === entry.id && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-white/95 backdrop-blur-sm z-20 flex items-center justify-center p-4 rounded-lg"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="text-center">
                      <AlertTriangle size={24} className="text-red-500 mx-auto mb-2" />
                      <p className="text-sm font-medium mb-1">Удалить запись?</p>
                      <p className="text-xs text-slate-500 mb-3">
                        {entry.date}
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDeleteEntry(entry.id)}
                          disabled={deleting === entry.id}
                          className="px-3 py-1.5 bg-red-600 text-white text-xs rounded-lg hover:bg-red-700 disabled:bg-red-300 flex items-center gap-1"
                        >
                          {deleting === entry.id ? (
                            <>
                              <RefreshCw size={12} className="animate-spin" />
                              Удаление...
                            </>
                          ) : (
                            'Удалить'
                          )}
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="px-3 py-1.5 bg-slate-200 text-slate-700 text-xs rounded-lg hover:bg-slate-300"
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Основной контент записи */}
              <div
                onClick={() => onSelectEntry(entry)}
                className="p-3 cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    entry.compliance_score >= 90 ? 'bg-green-100' :
                    entry.compliance_score >= 70 ? 'bg-amber-100' : 'bg-red-100'
                  }`}>
                    {getStatusIcon(entry.status)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Calendar size={12} />
                        {entry.date}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        entry.compliance_score >= 90 ? 'bg-green-100 text-green-700' :
                        entry.compliance_score >= 70 ? 'bg-amber-100 text-amber-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {entry.compliance_score}%
                      </span>
                    </div>
                    
                    <p className="text-sm text-slate-700 line-clamp-2">
                      {entry.diagnosis || 'Диагноз не указан'}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-slate-400 shrink-0" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Индикатор загрузки при обновлении */}
      {loading && history.length > 0 && (
        <div className="p-2 text-center border-t">
          <div className="inline-flex items-center gap-2 text-xs text-teal-600">
            <RefreshCw size={12} className="animate-spin" />
            Обновление...
          </div>
        </div>
      )}
    </div>
  );
}