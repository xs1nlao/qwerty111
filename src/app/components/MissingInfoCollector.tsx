import { motion, AnimatePresence } from "motion/react";
import { 
  AlertCircle, X, ChevronRight, CheckCircle, 
  HelpCircle, ArrowRight, Info, RefreshCw, ChevronLeft,
  User, Stethoscope
} from "lucide-react";
import { useState, useEffect, useMemo } from "react";

interface MissingInfoField {
  id: string;
  question: string;
  description: string;
  type: 'select' | 'textarea' | 'multiselect' | 'line_info'; 
  options?: string[];
  required: boolean;
  impacts_score: boolean;
  impacts_recommendations: boolean;
  category: 'treatment' | 'prognosis' | 'biomarker' | 'line_therapy'; 
  line_number?: number;
}

interface MissingInfoCollectorProps {
  patientId: string;
  missingInfo: any;
  originalHistory?: string;
  cancerType?: string;
  userType: "doctor" | "patient";
  onComplete: (answers: Record<string, string>, impactsScore: boolean) => void;
  onClose: () => void;
}

export function MissingInfoCollector({ 
  patientId, 
  missingInfo, 
  originalHistory = '',
  cancerType = '',
  userType,
  onComplete, 
  onClose 
}: MissingInfoCollectorProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);

  const isDoctor = userType === "doctor";
  const isPatient = userType === "patient";

  // Нормализуем поля
  const fields = useMemo(() => {
    if (!missingInfo) return [];
    const rawFields = missingInfo.fields || missingInfo;
    return Array.isArray(rawFields) ? rawFields : [];
  }, [missingInfo]);

  const currentField = fields[currentStep];

  const handleAnswer = (fieldId: string, value: string) => {
    if (currentField) {
      setAnswers(prev => ({
        ...prev,
        [fieldId]: value
      }));
    }
  };

  const isCurrentAnswered = () => {
    if (!currentField) return false;
    if (!currentField.required) return true;
    return !!answers[currentField.id] || !!answers[`${currentField.id}_custom`];
  };

  const handleNext = () => {
    if (currentStep < fields.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

 
  const handleSubmit = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      console.log("📤 Отправка answers:", answers);
      
  
      const impactsScore = fields.some(field => 
        field.impacts_score && answers[field.id]
      );
      
      const response = await fetch('http://localhost:5000/api/update-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientId: patientId,
          answers: answers,
          originalHistory: originalHistory,
          cancerType: cancerType
        })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log("✅ Анализ обновлен");
        setCompleted(true);
        
        setTimeout(() => {
          onComplete(answers, impactsScore);
        }, 1500);
      } else {
        alert('Ошибка при обновлении анализа: ' + data.error);
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error('❌ Ошибка:', error);
      alert('Ошибка при отправке данных');
      setIsSubmitting(false);
    }
  };

  if (!fields || fields.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <div className="bg-white rounded-2xl p-8 max-w-md text-center">
          <AlertCircle size={48} className="text-amber-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Нет вопросов</h3>
          <button onClick={onClose} className="px-6 py-2 bg-amber-600 text-white rounded-lg">
            Закрыть
          </button>
        </div>
      </motion.div>
    );
  }

  const progress = ((currentStep + 1) / fields.length) * 100;

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
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Заголовок */}
        <div className="p-6 border-b bg-gradient-to-r from-amber-600 to-amber-700 text-white">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              {isDoctor ? <Stethoscope size={24} /> : <User size={24} />}
              <div>
                <h2 className="text-2xl font-bold">
                  {isDoctor ? 'Уточните информацию' : 'Ответьте на вопросы'}
                </h2>
                <p className="text-amber-100 text-sm">
                  {isDoctor 
                    ? 'Введите данные своими словами' 
                    : 'Выберите подходящий вариант'}
                </p>
                <p className="text-amber-200 text-xs mt-1">
                  Вопрос {currentStep + 1} из {fields.length}
                </p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-amber-500 rounded-lg">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Прогресс */}
        <div className="h-2 bg-slate-100">
          <div 
            className="h-full transition-all bg-amber-500"
            style={{ width: `${progress}%` }} 
          />
        </div>

        {/* Контент */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {currentField && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl border bg-amber-50 border-amber-200">
                <p className="font-medium mb-1 text-amber-800">
                  {currentField.question}
                </p>
                <p className="text-sm text-amber-700">
                  {currentField.description}
                </p>
                {currentField.impacts_score && (
                  <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                    <AlertCircle size={12} />
                    Этот ответ может повлиять на оценку соответствия лечению
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {isDoctor ? 'Ваш ответ' : 'Выберите вариант'} 
                  {currentField.required && <span className="text-red-500 ml-1">*</span>}
                </label>

                {/* ДЛЯ ПАЦИЕНТА */}
                {isPatient && (
                  <div className="space-y-3">
                    {currentField.type === 'select' && currentField.options && currentField.options.length > 0 ? (
                      currentField.options.map((opt, idx) => (
                        <label
                          key={idx}
                          className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                            answers[currentField.id] === opt
                              ? 'bg-amber-100 border-amber-500'
                              : 'hover:bg-amber-50 border-slate-200'
                          }`}
                        >
                          <input
                            type="radio"
                            name={currentField.id}
                            value={opt}
                            checked={answers[currentField.id] === opt}
                            onChange={(e) => handleAnswer(currentField.id, e.target.value)}
                            className="mr-3 text-amber-600"
                          />
                          <span>{opt}</span>
                        </label>
                      ))
                    ) : (
                      <textarea
                        value={answers[currentField.id] || ''}
                        onChange={(e) => handleAnswer(currentField.id, e.target.value)}
                        className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-amber-300 min-h-[100px]"
                        placeholder="Введите ваш ответ..."
                      />
                    )}
                  </div>
                )}

                {/* ДЛЯ ВРАЧА */}
                {isDoctor && (
                  <textarea
                    value={answers[currentField.id] || ''}
                    onChange={(e) => handleAnswer(currentField.id, e.target.value)}
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-amber-300 min-h-[100px]"
                    placeholder="Введите информацию..."
                  />
                )}
              </div>

              {currentField.help_text && (
                <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                  <Info size={16} className="inline mr-1" />
                  {currentField.help_text}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Кнопки */}
        <div className="p-6 border-t bg-slate-50">
          <div className="flex justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="flex items-center gap-1 px-4 py-2 text-slate-600 disabled:text-slate-300"
            >
              <ChevronLeft size={16} /> Назад
            </button>
            
            <button
              onClick={handleNext}
              disabled={!isCurrentAnswered() || isSubmitting}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg text-white ${
                isCurrentAnswered() && !isSubmitting
                  ? 'bg-amber-600 hover:bg-amber-700' 
                  : 'bg-slate-300 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Отправка...
                </>
              ) : currentStep === fields.length - 1 ? (
                'Завершить'
              ) : (
                <>
                  Далее <ChevronRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}