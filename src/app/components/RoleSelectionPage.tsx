import { motion } from "motion/react";
import { Stethoscope, User, ArrowRight, Shield, Activity } from "lucide-react";
import { useState } from "react";

interface RoleSelectionPageProps {
  onSelectRole: (role: "doctor" | "patient") => void;
}

export function RoleSelectionPage({ onSelectRole }: RoleSelectionPageProps) {
  const [selectedRole, setSelectedRole] = useState<"doctor" | "patient" | null>(null);
  const [hoveredRole, setHoveredRole] = useState<"doctor" | "patient" | null>(null);

  const handleContinue = () => {
    if (selectedRole) {
      onSelectRole(selectedRole);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-slate-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl w-full"
      >
        {/* Логотип */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="inline-block bg-teal-600 p-4 rounded-2xl text-white mb-4"
          >
            <Activity size={48} />
          </motion.div>
          <h1 className="text-4xl font-bold text-slate-800 mb-2">
            QWERTY<span className="text-teal-600">123</span> AI
          </h1>
          <p className="text-slate-600 text-lg">
            AI-помощник для проверки лечения онкологических заболеваний
          </p>
        </div>

        {/* Карточки выбора роли (без изменений) */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Врач */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelectedRole("doctor")}
            onMouseEnter={() => setHoveredRole("doctor")}
            onMouseLeave={() => setHoveredRole(null)}
            className={`
              cursor-pointer rounded-2xl p-8 border-2 transition-all
              ${selectedRole === "doctor" 
                ? "border-teal-600 bg-teal-50 shadow-xl" 
                : "border-slate-200 bg-white hover:border-teal-300 hover:shadow-lg"}
            `}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`
                w-20 h-20 rounded-2xl flex items-center justify-center mb-4 transition-all
                ${selectedRole === "doctor" 
                  ? "bg-teal-600 text-white" 
                  : "bg-teal-100 text-teal-600"}
              `}>
                <Stethoscope size={40} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Врач</h2>
              <p className="text-slate-600 mb-4">
                Полный доступ к пациентам, истории проверок, детальный анализ
              </p>
              <ul className="text-sm text-slate-500 space-y-2">
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>Управление списком пациентов</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>Детальный разбор назначений</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>Сравнение с гайдлайнами</span>
                </li>
              </ul>
            </div>
          </motion.div>

          {/* Пациент */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelectedRole("patient")}
            onMouseEnter={() => setHoveredRole("patient")}
            onMouseLeave={() => setHoveredRole(null)}
            className={`
              cursor-pointer rounded-2xl p-8 border-2 transition-all
              ${selectedRole === "patient" 
                ? "border-teal-600 bg-teal-50 shadow-xl" 
                : "border-slate-200 bg-white hover:border-teal-300 hover:shadow-lg"}
            `}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`
                w-20 h-20 rounded-2xl flex items-center justify-center mb-4 transition-all
                ${selectedRole === "patient" 
                  ? "bg-teal-600 text-white" 
                  : "bg-teal-100 text-teal-600"}
              `}>
                <User size={40} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Пациент</h2>
              <p className="text-slate-600 mb-4">
                Проверка своего лечения, понятные объяснения, история проверок
              </p>
              <ul className="text-sm text-slate-500 space-y-2">
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>Простой язык без терминов</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>История своих проверок</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-teal-400 rounded-full"></div>
                  <span>Вопросы для врача</span>
                </li>
              </ul>
            </div>
          </motion.div>
        </div>

        {/* Кнопка продолжения */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: selectedRole ? 1 : 0.5 }}
          className="text-center"
        >
          <button
            onClick={handleContinue}
            disabled={!selectedRole}
            className={`
              inline-flex items-center gap-3 px-8 py-4 rounded-xl text-lg font-bold transition-all
              ${selectedRole
                ? "bg-teal-600 text-white hover:bg-teal-700 hover:shadow-xl hover:-translate-y-1" 
                : "bg-slate-200 text-slate-400 cursor-not-allowed"}
            `}
          >
            <span>Продолжить как {selectedRole === "doctor" ? "врач" : selectedRole === "patient" ? "пациент" : ""}</span>
            <ArrowRight size={20} />
          </button>
        </motion.div>

        {/* Анонимность */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <div className="inline-flex items-center gap-2 text-sm text-slate-400">
            <Shield size={16} />
            <span>Все данные обрабатываются анонимно</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}