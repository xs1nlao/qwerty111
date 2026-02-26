import { Upload, AlertCircle, Shield, UserX, FileText, X, Paperclip, User } from "lucide-react";
import { motion } from "motion/react";
import { useRef, useState } from "react";

interface InputSectionProps {
  userType: "doctor" | "patient";
  historyInput: string;
  setHistoryInput: (value: string) => void;
  onAnalyze: (files?: File[]) => void;
  selectedPatient: string | null;
  patientId?: string;
  patientHistory?: any[];
  isAnalyzing?: boolean;
}

export function InputSection({ 
  userType, 
  historyInput, 
  setHistoryInput, 
  onAnalyze,
  selectedPatient,
  patientId,
  isAnalyzing = false
}: InputSectionProps) {
  
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasText = historyInput.trim().length >= 10;
  const hasFiles = uploadedFiles.length > 0;
  const canAnalyze = (hasText || hasFiles) && 
    (userType === "patient" || (userType === "doctor" && selectedPatient)) && 
    !isAnalyzing;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError(null);
    
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      
      const oversizedFiles = newFiles.filter(f => f.size > 10 * 1024 * 1024);
      if (oversizedFiles.length > 0) {
        setFileError(`Файл ${oversizedFiles[0].name} превышает 10 MB`);
        return;
      }
      
      const invalidFiles = newFiles.filter(f => 
        !f.name.endsWith('.pdf') && 
        !f.name.endsWith('.docx') && 
        !f.name.endsWith('.doc') && 
        !f.name.endsWith('.txt')
      );
      
      if (invalidFiles.length > 0) {
        setFileError('Поддерживаются только PDF, DOCX, DOC и TXT файлы');
        return;
      }
      
      setUploadedFiles([...uploadedFiles, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(uploadedFiles.filter((_, i) => i !== index));
    setFileError(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleAnalyzeClick = () => {
    if (!hasText && !hasFiles) {
      alert("Введите историю болезни или прикрепите файлы");
      return;
    }
    
    if (userType === "doctor" && !selectedPatient) {
      alert("Сначала выберите пациента из списка");
      return;
    }
    
    onAnalyze(uploadedFiles);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto"
    >
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">
          Проверка лечения
        </h1>
        <p className="text-slate-600">
          {userType === "doctor" 
            ? "Детальный анализ для врача"
            : "Проверьте правильность своего лечения"}
        </p>
      </div>

      {userType === "patient" && patientId && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2">
            <User size={18} className="text-blue-600" />
            <span className="text-sm text-blue-800">
              Ваш ID: <span className="font-mono font-bold">{patientId}</span>
            </span>
          </div>
          <p className="text-xs text-blue-600 mt-1">
            Сохраните этот ID - он нужен для доступа к вашей истории
          </p>
        </div>
      )}

      {userType === "doctor" && selectedPatient && (
        <div className="mb-4 p-4 bg-teal-50 rounded-xl border border-teal-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center text-white font-bold">
              {selectedPatient.slice(-2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-teal-800">
                Пациент: {selectedPatient}
              </p>
              <p className="text-xs text-teal-600">
                Выбран для анализа
              </p>
            </div>
          </div>
        </div>
      )}

      {userType === "doctor" && !selectedPatient && (
        <div className="mb-4 p-4 bg-amber-50 rounded-xl border border-amber-200">
          <div className="flex items-center gap-3">
            <UserX size={20} className="text-amber-600" />
            <div>
              <p className="text-sm font-medium text-amber-800">Пациент не выбран</p>
              <p className="text-xs text-amber-600">
                Выберите пациента из списка слева или добавьте нового
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
        <textarea
          value={historyInput}
          onChange={(e) => setHistoryInput(e.target.value)}
          placeholder={userType === "doctor" && !selectedPatient 
            ? "Сначала выберите пациента..." 
            : "Вставьте историю болезни или опишите случай..."}
          disabled={userType === "doctor" && !selectedPatient}
          className={`w-full h-48 p-4 text-slate-700 resize-none focus:outline-none text-sm ${
            userType === "doctor" && !selectedPatient ? "bg-slate-50 cursor-not-allowed" : ""
          }`}
        />

        <div className="border-t border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Paperclip size={14} />
              Прикрепить файлы (PDF, DOCX, TXT)
            </span>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc,.txt"
              multiple
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={userType === "doctor" && !selectedPatient}
              className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg transition-all ${
                userType === "doctor" && !selectedPatient
                  ? "bg-slate-300 text-slate-500 cursor-not-allowed"
                  : "bg-teal-600 text-white hover:bg-teal-700"
              }`}
            >
              <Upload size={14} />
              Выбрать файлы
            </button>
          </div>
          
          {fileError && (
            <div className="mb-2 p-2 bg-red-50 rounded-lg flex items-center gap-2 text-xs text-red-600">
              <AlertCircle size={14} />
              {fileError}
            </div>
          )}
          
          {uploadedFiles.length > 0 && (
            <div className="space-y-2 max-h-32 overflow-y-auto p-2 bg-white rounded-lg border border-slate-200">
              {uploadedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between group hover:bg-slate-50 p-1 rounded">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText size={14} className="text-teal-600 shrink-0" />
                    <span className="text-xs truncate max-w-[200px]" title={file.name}>
                      {file.name}
                    </span>
                    <span className="text-xs text-slate-400 shrink-0">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                  <button
                    onClick={() => removeFile(idx)}
                    className="p-1 hover:bg-red-100 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X size={14} className="text-red-500" />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {uploadedFiles.length > 0 && (
            <p className="text-xs text-teal-600 mt-2">
              ✓ Загружено {uploadedFiles.length} файл(ов)
            </p>
          )}
        </div>

        <div className="p-3 bg-slate-50 border-t flex justify-between items-center">
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <Shield size={14} className="text-slate-500" />
            <span>Анонимная обработка</span>
            {uploadedFiles.length > 0 && (
              <span className="ml-2 text-teal-600">
                • {uploadedFiles.length} файл(ов)
              </span>
            )}
          </div>
          
          <button
            onClick={handleAnalyzeClick}
            disabled={!canAnalyze || isAnalyzing}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              canAnalyze && !isAnalyzing
                ? "bg-teal-600 text-white hover:bg-teal-700 hover:shadow-md" 
                : "bg-slate-300 text-slate-500 cursor-not-allowed"
            }`}
          >
            {isAnalyzing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Анализ...
              </>
            ) : (
              'Проверить'
            )}
          </button>
        </div>
      </div>

      {userType === "patient" && (
        <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-start gap-2">
            <AlertCircle size={16} className="text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-700">
              <p className="font-medium mb-1">Важно:</p>
              <p>Данный анализ не заменяет консультацию врача. Результаты носят ознакомительный характер и должны быть интерпретированы специалистом.</p>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}