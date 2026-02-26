import { Activity, LogOut, BarChart3 } from "lucide-react";

interface HeaderProps {
  resetApp: () => void;
  onLogout: () => void;
  onShowMammogram?: () => void;
  onShowTreatment?: () => void;
  onShowMetrics?: () => void;
  showMetricsButton?: boolean;
}

export function Header({ resetApp, onLogout, onShowMetrics, onShowMammogram, showMetricsButton, onShowTreatment }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={resetApp}>
          <div className="bg-teal-600 p-2 rounded-lg text-white">
            <Activity size={24} />
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">
            QWERTY<span className="text-teal-600">123</span> AI
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onShowTreatment}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
          >
            <BarChart3 size={18} />
            <span className="hidden sm:inline">Проверка лечения</span>
          </button>
          
          <button
            onClick={onShowMammogram}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
          >
            <BarChart3 size={18} />
            <span className="hidden sm:inline">Анализ маммограммы</span>
          </button>
          
          {showMetricsButton && (
            <button
              onClick={onShowMetrics}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
            >
              <BarChart3 size={18} />
              <span className="hidden sm:inline">Статистика</span>
            </button>
          )}
          
          <button
            onClick={onLogout}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span className="hidden sm:inline">Выйти</span>
          </button>
        </div>
      </div>
    </header>
  );
}