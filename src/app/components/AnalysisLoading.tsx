import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";

const STEPS = [
  "Анализ структуры документа...",
  "Выделение ключевых параметров...",
  "Сверка с NCCN...",
  "Проверка рекомендаций ESMO...",
  "Сверка с AI...",
  "Генерация отчета..."
];

export function AnalysisLoading() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-md mx-auto px-6">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        className="mb-8 text-teal-600"
      >
        <Loader2 size={64} />
      </motion.div>

      <div className="w-full space-y-4">
        {STEPS.map((step, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ 
              opacity: index <= currentStep ? 1 : 0.3,
              x: index <= currentStep ? 0 : -10
            }}
            className="flex items-center gap-3"
          >
            <div className={`
              w-6 h-6 rounded-full flex items-center justify-center border transition-colors duration-300
              ${index < currentStep 
                ? "bg-teal-500 border-teal-500 text-white" 
                : index === currentStep 
                  ? "border-teal-500 text-teal-500 animate-pulse" 
                  : "border-slate-200 text-transparent"}
            `}>
              <Check size={14} strokeWidth={3} />
            </div>
            <span className={`
              text-sm font-medium transition-colors duration-300
              ${index <= currentStep ? "text-slate-800" : "text-slate-400"}
            `}>
              {step}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}