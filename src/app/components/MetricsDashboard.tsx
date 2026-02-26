import { motion } from "framer-motion";
import { 
  BarChart3, X, Activity, Clock, CheckCircle, AlertTriangle,
  TrendingUp, TrendingDown, Minus, Calendar, Zap, Database,
  Camera, FileText
} from "lucide-react";
import { useState, useEffect } from "react";

export function MetricsDashboard({ onClose }: { onClose: () => void }) {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("📊 Загрузка метрик...");
      const response = await fetch('http://localhost:5000/api/metrics');
      const data = await response.json();
      console.log("📊 Метрики загружены:", data);
      
      if (data.success) {
        setMetrics(data.metrics);
      } else {
        setError(data.error || 'Ошибка загрузки метрик');
      }
    } catch (error) {
      console.error('❌ Error loading metrics:', error);
      setError('Ошибка соединения с сервером');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 65) return 'text-amber-600';
    return 'text-red-600';
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Заголовок */}
        <div className="p-6 border-b bg-gradient-to-r from-teal-600 to-blue-600 text-white flex justify-between items-center">
          <div className="flex items-center gap-3">
            <BarChart3 size={28} />
            <div>
              <h2 className="text-2xl font-bold">Статистика системы</h2>
              <p className="text-teal-100 text-sm">Мониторинг производительности и качества</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-teal-500 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Контент */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-teal-200 border-t-teal-600 mb-4"></div>
              <p className="text-slate-500">Загрузка метрик...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 p-6 rounded-xl text-center">
              <AlertTriangle size={48} className="text-red-500 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-red-800 mb-2">Ошибка загрузки</h3>
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={loadMetrics}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Повторить
              </button>
            </div>
          ) : metrics ? (
            <div className="space-y-6">
              {/* Период */}
              <div className="bg-slate-50 p-4 rounded-xl flex items-center gap-3 text-slate-600">
                <Calendar size={20} className="text-teal-600" />
                <span className="text-sm">
                  Период: {metrics.period.start} — {metrics.period.end} 
                  ({metrics.period.days} {metrics.period.days === 1 ? 'день' : 
                    metrics.period.days < 5 ? 'дня' : 'дней'})
                </span>
              </div>

              {/* Основные метрики */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-5 rounded-xl border border-teal-200">
                  <Activity className="text-teal-600 mb-2" size={28} />
                  <div className="text-3xl font-bold text-teal-800">
                    {formatNumber(metrics.volume.total_analyses)}
                  </div>
                  <div className="text-sm text-teal-600">Всего проверок лечения</div>
                  <div className="text-xs text-teal-500 mt-1">
                    {metrics.volume.analyses_per_day} в день
                  </div>
                </div>
                
                <div className={`p-5 rounded-xl border ${
                  metrics.quality.avg_compliance_score >= 85 ? 'bg-green-50 border-green-200' :
                  metrics.quality.avg_compliance_score >= 65 ? 'bg-amber-50 border-amber-200' :
                  'bg-red-50 border-red-200'
                }`}>
                  <CheckCircle className={`mb-2 ${
                    metrics.quality.avg_compliance_score >= 85 ? 'text-green-600' :
                    metrics.quality.avg_compliance_score >= 65 ? 'text-amber-600' :
                    'text-red-600'
                  }`} size={28} />
                  <div className={`text-3xl font-bold ${
                    metrics.quality.avg_compliance_score >= 85 ? 'text-green-600' :
                    metrics.quality.avg_compliance_score >= 65 ? 'text-amber-600' :
                    'text-red-600'
                  }`}>
                    {metrics.quality.avg_compliance_score}%
                  </div>
                  <div className="text-sm text-slate-600">Средняя оценка соответствия требованиям</div>
                  <div className="flex gap-1 mt-2 text-xs">
                    <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                      Высоких: {metrics.quality.score_distribution.high}
                    </span>
                    <span className="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                      Средних: {metrics.quality.score_distribution.medium}
                    </span>
                    <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                      Низких: {metrics.quality.score_distribution.low}
                    </span>
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-5 rounded-xl border border-blue-200">
                  <Clock className="text-blue-600 mb-2" size={28} />
                  <div className="text-3xl font-bold text-blue-800">{metrics.performance.avg_response_time}с</div>
                  <div className="text-sm text-blue-600">Среднее время ответа</div>
                  <div className="text-xs text-blue-500 mt-1">
                    мин: {metrics.performance.min_response_time}с / макс: {metrics.performance.max_response_time}с
                  </div>
                </div>
              </div>

              {/* Маммограммы */}
              {metrics.mammogram && metrics.mammogram.total > 0 && (
                <div className="bg-white p-5 rounded-xl border border-slate-200">
                  <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                    <Camera size={18} className="text-teal-600" />
                    Анализ маммограмм
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-slate-700">{metrics.mammogram.total}</div>
                      <div className="text-xs text-slate-500">Всего анализов</div>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{metrics.mammogram.malignant}</div>
                      <div className="text-xs text-slate-500">Злокачественные</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{metrics.mammogram.benign}</div>
                      <div className="text-xs text-slate-500">Доброкачественные</div>
                    </div>
                    <div className="text-center p-3 bg-teal-50 rounded-lg">
                      <div className="text-2xl font-bold text-teal-600">
                        {(metrics.mammogram.avg_confidence * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-slate-500">Ср. уверенность</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Ошибки */}
              {metrics.errors.total > 0 ? (
                <div className="bg-red-50 p-5 rounded-xl border border-red-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={18} className="text-red-600" />
                      <h3 className="font-semibold text-red-800">Ошибки системы</h3>
                    </div>
                    <span className="text-sm text-red-700">
                      Частота: {metrics.errors.error_rate}%
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold text-red-700">
                    {metrics.errors.total} {metrics.errors.total === 1 ? 'ошибка' : 
                      metrics.errors.total < 5 ? 'ошибки' : 'ошибок'}
                  </div>
                </div>
              ) : (
                <div className="bg-green-50 p-4 rounded-xl border border-green-200 text-green-700 flex items-center gap-2">
                  <CheckCircle size={18} />
                  <span className="text-sm">Система работает без ошибок</span>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <BarChart3 size={48} className="mx-auto mb-3 text-slate-300" />
              <p>Нет данных для отображения</p>
              <p className="text-xs mt-2">Выполните несколько проверок, чтобы увидеть статистику</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}