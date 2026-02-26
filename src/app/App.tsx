
import { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { InputSection } from "./components/InputSection";
import { AnalysisLoading } from "./components/AnalysisLoading";
import { ResultsView } from "./components/ResultsView";
import { DoctorPatients } from "./components/DoctorPatients";
import { PatientHistory } from "./components/PatientHistory";
import { RoleSelectionPage } from "./components/RoleSelectionPage";
import { MammogramAnalyzer } from "./components/MammogramAnalyzer";
import { MetricsDashboard } from "./components/MetricsDashboard";
import { Stethoscope, User, Activity } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

export default function App() {
  const [role, setRole] = useState<"doctor" | "patient" | null>(null);
  const [userType, setUserType] = useState<"doctor" | "patient">("doctor");
  const [view, setView] = useState<"input" | "processing" | "results">("input");
  const [historyInput, setHistoryInput] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<string | null>(null);
  const [currentResult, setCurrentResult] = useState<any>(null);
  const [patientId, setPatientId] = useState<string>("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<"treatment" | "mammogram">("treatment");
  const [showMetrics, setShowMetrics] = useState(false);

  useEffect(() => {
    const savedPatientId = localStorage.getItem('patientId');
    if (savedPatientId) {
      setPatientId(savedPatientId);
    } else {
      const newPatientId = 'patient-' + Math.random().toString(36).substring(2, 10);
      localStorage.setItem('patientId', newPatientId);
      setPatientId(newPatientId);
    }
  }, []);

  useEffect(() => {
    if (role) {
      setUserType(role);
      if (role === "patient") {
        setSelectedPatient(patientId);
      } else {
        setSelectedPatient(null);
      }
    }
  }, [role, patientId]);

  if (!role) {
    return <RoleSelectionPage onSelectRole={setRole} />;
  }

  const handleAnalyze = async (files?: File[]) => {
    if (userType === "doctor" && !selectedPatient) {
      alert("Сначала выберите пациента из списка");
      return;
    }

    if (!historyInput && (!files || files.length === 0)) {
      alert("Введите историю болезни или прикрепите файлы");
      return;
    }

    setIsAnalyzing(true);
    setView("processing");
    
    try {
      const targetPatientId = userType === "doctor" ? selectedPatient : patientId;
      
      let response;
      
      if (files && files.length > 0) {
        const formData = new FormData();
        formData.append('history', historyInput);
        formData.append('patient_id', targetPatientId || '');
        
        files.forEach((file) => {
          formData.append('files', file);
        });
        
        response = await fetch('http://localhost:5000/api/check-treatment-with-files', {
          method: 'POST',
          body: formData
        });
      } else {
        const requestData = { 
          history: historyInput,
          patient_id: targetPatientId
        };
        
        response = await fetch('http://localhost:5000/api/check-treatment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData)
        });
      }
      
      const data = await response.json();
      
      if (data.success) {
        setCurrentResult(data.result);
        localStorage.setItem('aiResult', JSON.stringify(data.result));
        
        if (data.patient_id && userType === "patient" && data.patient_id !== patientId) {
          localStorage.setItem('patientId', data.patient_id);
          setPatientId(data.patient_id);
        }
        
        setView("results");
        
        if (userType === "doctor" && selectedPatient) {
          window.dispatchEvent(new CustomEvent('patient-updated'));
        }
      } else {
        alert('Ошибка при проверке: ' + data.error);
        setView("input");
      }
      
    } catch (error) {
      alert('Ошибка при проверке. Проверьте подключение к серверу.');
      setView("input");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectPatient = (patientId: string | null) => {
    setSelectedPatient(patientId);
    setHistoryInput("");
  };

  const handleSelectHistoryEntry = (entry: any) => {
    if (entry.full_result) {
      setCurrentResult(entry.full_result);
      localStorage.setItem('aiResult', JSON.stringify(entry.full_result));
      setView("results");
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/patient/${patientId}/history/${entryId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        window.dispatchEvent(new CustomEvent('patient-history-updated'));
      }
    } catch (error) {
      console.error("Ошибка удаления записи:", error);
    }
  };

  const handleClearHistory = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/patient/${patientId}/history/clear`, {
        method: 'POST'
      });
      
      if (response.ok) {
        window.dispatchEvent(new CustomEvent('patient-history-updated'));
      }
    } catch (error) {
      console.error("Ошибка очистки истории:", error);
    }
  };

  const handleReset = () => {
    setView("input");
    setHistoryInput("");
  };

  const handleSwitchMode = () => {
    const newMode = userType === "doctor" ? "patient" : "doctor";
    setUserType(newMode);
    setView("input");
    setHistoryInput("");
    
    if (newMode === "patient") {
      setSelectedPatient(patientId);
    } else {
      setSelectedPatient(null);
    }
  };

  const handleLogout = () => {
    setRole(null);
    setView("input");
    setHistoryInput("");
    setSelectedPatient(null);
    setCurrentResult(null);
    setShowMetrics(false);
  };

  const handleBackToInput = () => {
    setView("input");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Header 
        resetApp={handleReset} 
        onLogout={handleLogout}
        onShowMetrics={() => setShowMetrics(true)}
        onShowMammogram={() => {
          setActiveTab('mammogram');
          setView('input');
        }}
        onShowTreatment={() => {
          setActiveTab('treatment');
          setView('input');
        }}
        showMetricsButton={userType === "doctor"}
      />
      
      <main className="container mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          {view === "input" && (
            <motion.div
              key="input"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex gap-6"
            >
              <div className="w-80 shrink-0 space-y-4">
                <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {userType === "doctor" ? (
                        <Stethoscope size={18} className="text-teal-600" />
                      ) : (
                        <User size={18} className="text-teal-600" />
                      )}
                      <span className="font-medium">
                        {userType === "doctor" ? "Режим врача" : "Режим пациента"}
                      </span>
                    </div>
                    <button
                      onClick={handleSwitchMode}
                      className="text-xs text-teal-600 hover:text-teal-700 px-2 py-1 bg-teal-50 rounded"
                    >
                      Сменить
                    </button>
                  </div>
                </div>

                {userType === "doctor" ? (
                  <DoctorPatients 
                    onSelectPatient={handleSelectPatient}
                    selectedPatientId={selectedPatient}
                  />
                ) : (
                  <PatientHistory 
                    patientId={patientId}
                    onSelectEntry={handleSelectHistoryEntry}
                    userType={userType}
                    showId={true}
                    onDeleteEntry={handleDeleteEntry} 
                    onClearHistory={handleClearHistory} 
                  />
                )}
              </div>

              <div className="flex-1">
                {activeTab === "treatment" ? (
                  <InputSection 
                    userType={userType}
                    historyInput={historyInput} 
                    setHistoryInput={setHistoryInput} 
                    onAnalyze={handleAnalyze}
                    selectedPatient={selectedPatient}
                    patientId={patientId}
                    isAnalyzing={isAnalyzing}
                  />
                ) : (
                  <MammogramAnalyzer patientId={patientId} />
                )}
              </div>
            </motion.div>
          )}

          {view === "processing" && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 bg-white z-50 flex items-center justify-center"
            >
              <AnalysisLoading />
            </motion.div>
          )}

          {view === "results" && (
            <motion.div
              key="results"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 bg-white z-50 overflow-y-auto"
            >
              <div className="container mx-auto px-4 py-6">
                <button
                  onClick={handleBackToInput}
                  className="mb-4 flex items-center gap-2 text-teal-600 hover:text-teal-700 transition-colors"
                >
                  <span>←</span>
                  <span>Вернуться к вводу</span>
                </button>
                
                <ResultsView userType={userType} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      
      <AnimatePresence>
        {showMetrics && (
          <MetricsDashboard onClose={() => setShowMetrics(false)} />
        )}
      </AnimatePresence>
      
      <footer className="py-6 text-center text-slate-400 text-xs border-t border-slate-200 mt-8">
        <p>© 2026 QWERTY123 AI. Не является заменой профессиональной медицинской консультации.</p>
        {userType === "patient" && patientId && (
          <p className="mt-1 text-xs text-slate-300">
            Ваш ID: <span className="font-mono">{patientId}</span>
          </p>
        )}
      </footer>
    </div>
  );
}
