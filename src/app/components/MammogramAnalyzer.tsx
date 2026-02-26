import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Activity, AlertCircle, CheckCircle, 
  X, RefreshCw, Shield, Camera, Info 
} from 'lucide-react';

interface PredictionResult {
  is_malignant: boolean;
  label: string;
  confidence: number;
  probability: number;
}

interface MammogramResponse {
  success: boolean;
  result?: PredictionResult;
  model_info?: {
    accuracy: number;
    type: string;
    note?: string;
  };
  patient_id?: string;
  error?: string;
}

export function MammogramAnalyzer({ patientId }: { patientId: string }) {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MammogramResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setError(null);
      setResult(null);
    }
  };

  const clearImage = () => {
    setImage(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const analyze = async () => {
    if (!image) {
      setError('Выберите файл для анализа');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    const formData = new FormData();
    formData.append('file', image);
    if (patientId) {
      formData.append('patient_id', patientId);
    }

    try {
      console.log("📤 Отправка запроса на анализ маммограммы...");
      const response = await fetch('http://localhost:5000/api/mammogram/analyze', {
        method: 'POST',
        body: formData
      });
      
      console.log("📥 Статус ответа:", response.status);
      const data = await response.json();
      console.log("📊 Данные от сервера:", data);
      
      if (data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Ошибка при анализе');
      }
    } catch (err) {
      console.error('❌ Analysis failed:', err);
      setError('Ошибка соединения с сервером. Проверьте, запущен ли бэкенд на порту 5000.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
      {/* Заголовок */}
      <div className="bg-gradient-to-r from-teal-600 to-blue-600 p-6 text-white">
        <div className="flex items-center gap-3">
          <Camera size={28} />
          <div>
            <h2 className="text-2xl font-bold">Анализ маммограммы</h2>
            <p className="text-teal-100 text-sm mt-1">
              AI-модель для выявления рака молочной железы
            </p>
          </div>
        </div>
        {result?.model_info && (
          <div className="mt-3 flex items-center gap-2 text-xs bg-white/20 px-3 py-1.5 rounded-full w-fit">
            <Activity size={12} />
            <span>Модель: {result.model_info.type}</span>
          </div>
        )}
      </div>

      <div className="p-6">
        {/* Область загрузки */}
        <div className={`border-2 border-dashed rounded-xl p-8 transition-all ${
          preview ? 'border-teal-300 bg-teal-50/50' : 'border-slate-200 hover:border-teal-300 hover:bg-slate-50'
        }`}>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
            id="mammogram-upload"
          />
          
          {!preview ? (
            <label
              htmlFor="mammogram-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <div className="w-20 h-20 bg-teal-100 rounded-full flex items-center justify-center mb-4">
                <Upload size={32} className="text-teal-600" />
              </div>
              <p className="text-lg font-medium text-slate-700 mb-2">
                Загрузите маммограмму
              </p>
              <p className="text-sm text-slate-500 text-center mb-4">
                Поддерживаются форматы JPG, PNG<br/>
                Для лучших результатов используйте изображения высокого качества
              </p>
              <div className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors shadow-md hover:shadow-lg">
                Выбрать файл
              </div>
            </label>
          ) : (
            <div className="relative">
              <img 
                src={preview} 
                alt="Preview" 
                className="max-h-96 mx-auto rounded-lg shadow-lg"
              />
              <button
                onClick={clearImage}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors shadow-lg"
              >
                <X size={16} />
              </button>
              
              <button
                onClick={analyze}
                disabled={loading}
                className={`mt-4 w-full py-3 rounded-lg text-white font-medium transition-all ${
                  loading 
                    ? 'bg-teal-400 cursor-not-allowed' 
                    : 'bg-teal-600 hover:bg-teal-700 shadow-lg hover:shadow-xl'
                }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <RefreshCw size={20} className="animate-spin" />
                    Анализ...
                  </span>
                ) : (
                  'Провести анализ'
                )}
              </button>
            </div>
          )}
        </div>

        {/* Ошибка */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200 text-red-700 flex items-start gap-3"
            >
              <AlertCircle className="shrink-0 mt-0.5" size={18} />
              <span className="text-sm">{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Результаты */}
        <AnimatePresence>
          {result && result.result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-8 space-y-6"
            >
              {/* Главный результат */}
              <div className={`p-6 rounded-xl border-2 ${
                result.result.is_malignant 
                  ? 'border-red-300 bg-red-50' 
                  : 'border-green-300 bg-green-50'
              }`}>
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${
                    result.result.is_malignant ? 'bg-red-200' : 'bg-green-200'
                  }`}>
                    {result.result.is_malignant ? (
                      <AlertCircle size={24} className="text-red-700" />
                    ) : (
                      <CheckCircle size={24} className="text-green-700" />
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-slate-800">
                      {result.result.is_malignant 
                        ? '⚠️ Обнаружены признаки злокачественного образования' 
                        : '✅ Признаков злокачественного образования не обнаружено'}
                    </h3>
                    
                    <div className="flex items-center gap-3 mt-4">
                      <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                        result.result.is_malignant 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {result.result.label}
                      </span>
                      
                      <div className="flex items-center gap-1 text-sm text-slate-600">
                        <Activity size={16} className="text-teal-600" />
                        <span className={getConfidenceColor(result.result.confidence)}>
                          Уверенность: {(result.result.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Прогресс-бар уверенности */}
                    <div className="mt-4">
                      <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${result.result.confidence * 100}%` }}
                          transition={{ duration: 0.5 }}
                          className={`h-3 rounded-full ${
                            result.result.is_malignant ? 'bg-red-500' : 'bg-green-500'
                          }`}
                        />
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-xs text-slate-500">Доброкачественно</span>
                        <span className="text-xs text-slate-500">Злокачественно</span>
                      </div>
                    </div>

                    {/* Вероятность */}
                    <div className="mt-3 text-xs text-slate-500">
                      Вероятность злокачественности: {(result.result.probability * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Информация о модели */}
              {result.model_info && (
                <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
                  <h4 className="font-medium text-slate-700 mb-3 flex items-center gap-2">
                    <Activity size={18} />
                    Информация об анализе
                  </h4>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-slate-500 block text-xs">Модель</span>
                      <span className="font-medium">{result.model_info.type}</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-slate-500 block text-xs">Точность</span>
                      <span className="font-medium text-teal-600">{result.model_info.accuracy}%</span>
                    </div>
                  </div>
                  {result.model_info.note && (
                    <p className="text-xs text-amber-600 mt-2">{result.model_info.note}</p>
                  )}
                </div>
              )}

              {/* Предупреждение */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
                <div className="flex items-start gap-3">
                  <Shield size={20} className="text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-amber-800 mb-1">
                      Важное предупреждение
                    </p>
                    <p className="text-xs text-amber-700 leading-relaxed">
                      Данный анализ является предварительным и не заменяет 
                      заключение врача-рентгенолога. Окончательный диагноз 
                      должен ставиться специалистом на основе полного обследования.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}