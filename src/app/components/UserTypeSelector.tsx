import { Stethoscope, User } from "lucide-react";
import { motion } from "motion/react";

interface UserTypeSelectorProps {
  userType: "doctor" | "patient";
  setUserType: (type: "doctor" | "patient") => void;
}

export function UserTypeSelector({ userType, setUserType }: UserTypeSelectorProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-white rounded-xl shadow-lg border border-slate-200 p-2"
    >
      <div className="flex gap-2">
        <button
          onClick={() => setUserType("doctor")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-all ${
            userType === "doctor"
              ? "bg-teal-600 text-white shadow-md"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Stethoscope size={18} />
          <span>Врач</span>
        </button>
        
        <button
          onClick={() => setUserType("patient")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-all ${
            userType === "patient"
              ? "bg-teal-600 text-white shadow-md"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <User size={18} />
          <span>Пациент</span>
        </button>
      </div>
    </motion.div>
  );
}