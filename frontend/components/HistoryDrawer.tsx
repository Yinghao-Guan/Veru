'use client';

import { X, Clock, Trash2, ArrowRight } from 'lucide-react';
import { useEffect } from 'react';
import { Translation } from '../translations'; // 引入类型定义

export interface AuditResult {
  citation_text: string;
  status: 'REAL' | 'FAKE' | 'MISMATCH' | 'UNVERIFIED' | 'SUSPICIOUS' | 'MINOR_ERROR';
  source: string;
  confidence: number;
  message: string;
  metadata?: any;
}

export interface HistoryItem {
  id: string;
  timestamp: number;
  inputText: string;
  results: AuditResult[];
}

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (item: HistoryItem) => void;
  history: HistoryItem[];
  onClear: () => void;
  t: Translation; // 接收翻译字典
}

export default function HistoryDrawer({ isOpen, onClose, onSelect, history, onClear, t }: HistoryDrawerProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />

      <div className="fixed top-0 right-0 h-full w-full sm:w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out border-l border-slate-200 flex flex-col">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <div className="flex items-center space-x-2 text-slate-700">
            <Clock className="w-5 h-5 text-blue-600" />
            <span className="font-bold text-lg">{t.historyTitle}</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-6">
              <Clock className="w-12 h-12 mb-3 opacity-20" />
              <p>{t.noHistoryTitle}</p>
              <p className="text-xs mt-1">{t.noHistoryDesc}</p>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelect(item);
                  onClose();
                }}
                className="group p-4 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-md cursor-pointer transition-all active:scale-98"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {new Date(item.timestamp).toLocaleDateString()} • {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-blue-500 transition-colors" />
                </div>
                <p className="text-sm text-slate-700 line-clamp-2 font-medium leading-relaxed">
                  "{item.inputText}"
                </p>
                <div className="mt-3 flex items-center space-x-2">
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">
                    {item.results.length} {t.citationsCount}
                  </span>
                  {item.results.some(r => r.status === 'FAKE') && (
                    <span className="text-[10px] bg-rose-50 text-rose-600 px-2 py-0.5 rounded-full border border-rose-100 font-bold">
                      {t.fakeDetected}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {history.length > 0 && (
          <div className="p-4 border-t border-slate-100 bg-slate-50/30">
            <button
              onClick={onClear}
              className="w-full flex items-center justify-center space-x-2 text-rose-600 hover:bg-rose-50 p-3 rounded-lg text-sm font-medium transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>{t.clearHistory}</span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}