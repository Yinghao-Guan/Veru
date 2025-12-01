'use client';

import { useState } from 'react';
import { BookOpen, AlertCircle, CheckCircle, Search, AlertTriangle, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// 定义 Logo 组件 (直接复用我们设计的 SVG)
function VeruLogo() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      className="w-8 h-8 mr-2" // 控制大小和间距
    >
      <defs>
        <linearGradient id="logo_grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#4F46E5', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#06B6D4', stopOpacity: 1 }} />
        </linearGradient>
      </defs>
      <rect width="512" height="512" rx="128" fill="url(#logo_grad)" />
      {/* V Shape / Checkmark (白色线条) */}
      <path
        d="M140 200 L210 340 L380 140"
        stroke="white"
        strokeWidth="64"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// 定义后端返回的数据结构
interface AuditResult {
  citation_text: string;
  status: 'REAL' | 'FAKE' | 'MISMATCH' | 'UNVERIFIED' | 'SUSPICIOUS';
  source: string;
  confidence: number;
  message: string;
  metadata?: any;
}

export default function Home() {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AuditResult[] | null>(null);

  const handleAudit = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setResults(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('API Error:', error);
      alert('无法连接到审计服务器，请检查后端是否启动');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-slate-800 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center">
            {/* 使用自定义 Logo 组件 */}
            <VeruLogo />
            <span className="text-xl font-bold tracking-tight text-slate-900">Veru</span>
          </div>
          <div className="text-xs font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            AI Citation Auditor
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-4rem)]">

        {/* Left Column: Input */}
        <div className="flex flex-col space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex-1 flex flex-col transition-all focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-300">
            <label className="text-sm font-semibold text-slate-700 mb-3 flex items-center">
              <Search className="w-4 h-4 mr-2 text-indigo-500" />
              Source Text (Paste ChatGPT response here)
            </label>
            <textarea
              className="flex-1 w-full p-4 bg-slate-50 border border-slate-200 rounded-lg outline-none resize-none font-mono text-sm leading-relaxed text-slate-700 placeholder:text-slate-400 focus:bg-white transition-colors"
              placeholder="Example: 'Smith (2023) argues that...'"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleAudit}
                disabled={loading || !inputText}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md active:transform active:scale-95"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Start Audit'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="flex flex-col space-y-4 overflow-y-auto pb-10">

          {/* 空状态：保留 BookOpen，因为它代表"准备好阅读文献" */}
          {!results && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                <BookOpen className="w-8 h-8 text-indigo-200" />
              </div>
              <p className="font-medium text-slate-500">Ready to audit</p>
              <p className="text-sm text-slate-400 mt-1">Paste text on the left to begin</p>
            </div>
          )}

          {/* 加载状态 */}
          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="text-center space-y-4">
                <div className="relative">
                  <div className="w-12 h-12 border-4 border-indigo-100 rounded-full animate-spin border-t-indigo-600"></div>
                </div>
                <p className="text-slate-500 text-sm font-medium animate-pulse">Running forensic analysis...</p>
              </div>
            </div>
          )}

          {/* 无结果状态 */}
          {results && results.length === 0 && (
             <div className="p-4 rounded-lg bg-orange-50 border border-orange-100 text-orange-800 flex items-start">
                <AlertTriangle className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                <div>
                    <p className="font-semibold text-sm">No citations detected</p>
                    <p className="text-xs mt-1 text-orange-700/80">Try pasting a text that contains references like "Author (Year)" or "Title by Author".</p>
                </div>
             </div>
          )}

          {/* 结果列表 */}
          {results && results.map((res, idx) => (
            <AuditCard key={idx} result={res} />
          ))}
        </div>
      </main>
    </div>
  );
}

// 审计卡片组件 (保持不变，或者微调样式)
function AuditCard({ result }: { result: AuditResult }) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'REAL':
        return { color: 'border-emerald-500 bg-emerald-50/30', icon: <CheckCircle className="w-5 h-5 text-emerald-600" />, text: 'text-emerald-700' };
      case 'FAKE':
        return { color: 'border-rose-500 bg-rose-50/30', icon: <AlertTriangle className="w-5 h-5 text-rose-600" />, text: 'text-rose-700' };
      case 'MISMATCH':
        return { color: 'border-amber-500 bg-amber-50/30', icon: <AlertCircle className="w-5 h-5 text-amber-600" />, text: 'text-amber-700' };
      default:
        return { color: 'border-slate-300 bg-slate-50', icon: <AlertCircle className="w-5 h-5 text-slate-500" />, text: 'text-slate-600' };
    }
  };

  const config = getStatusConfig(result.status);

  return (
    <div className={`p-5 rounded-xl border-l-4 shadow-sm bg-white transition-all hover:shadow-md ${config.color}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {config.icon}
          <span className={`font-bold text-sm tracking-wide uppercase ${config.text}`}>{result.status}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-100 text-slate-500 font-medium uppercase tracking-wider">
            {result.source}
          </span>
        </div>
        {result.confidence > 0 && (
            <div className="text-xs text-slate-400 font-mono" title="AI Confidence Score">
                {Math.round(result.confidence * 100)}% Conf.
            </div>
        )}
      </div>

      <div className="mb-4 text-sm font-medium text-slate-800 italic relative pl-4">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-slate-200 rounded-full"></div>
        "{result.citation_text.length > 120 ? result.citation_text.slice(0, 120) + '...' : result.citation_text}"
      </div>

      <div className="text-sm text-slate-600 leading-relaxed bg-white/60 p-3 rounded-lg border border-slate-100/50">
        <ReactMarkdown>{result.message}</ReactMarkdown>
      </div>

      {result.metadata?.title && (
         <div className="mt-4 pt-3 border-t border-slate-100 text-xs flex flex-col gap-1">
            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Source Match</span>
            <div className="text-slate-700 font-medium">
               {result.metadata.title} ({result.metadata.year})
            </div>
            {result.metadata.oa_url && (
                <a href={result.metadata.oa_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:text-indigo-800 hover:underline mt-1 inline-flex items-center transition-colors">
                    View Full Text <span className="ml-1">→</span>
                </a>
            )}
         </div>
      )}
    </div>
  );
}