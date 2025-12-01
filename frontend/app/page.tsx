'use client';

import { useState } from 'react';
import { BookOpen, AlertCircle, CheckCircle, Search, AlertTriangle, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

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
      // 调用你的 Python 后端
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
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-indigo-700">
            <BookOpen className="w-6 h-6" />
            <span className="text-xl font-bold tracking-tight">Truvio Audit</span>
          </div>
          <div className="text-sm text-slate-500">AI Hallucination Detector</div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-4rem)]">
        
        {/* Left Column: Input */}
        <div className="flex flex-col space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex-1 flex flex-col">
            <label className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
              <Search className="w-4 h-4 mr-2" />
              Source Text (Paste ChatGPT response here)
            </label>
            <textarea
              className="flex-1 w-full p-4 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none font-mono text-sm leading-relaxed"
              placeholder="Paste the text containing citations you want to verify..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleAudit}
                disabled={loading || !inputText}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Auditing...
                  </>
                ) : (
                  'Start Audit'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="flex flex-col space-y-4 overflow-y-auto">
          {/* 状态 1: 初始状态 (results 为 null) */}
          {!results && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
              <BookOpen className="w-12 h-12 mb-4 opacity-20" />
              <p>Audit results will appear here</p>
            </div>
          )}

          {/* 状态 2: 加载中 */}
          {loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-3">
                <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
                <p className="text-slate-500 text-sm">Analyzing citations against databases...</p>
              </div>
            </div>
          )}

          {/* === 🔴 新增状态 3: 结果为空 (找到了0篇文献) === */}
          {results && results.length === 0 && (
             <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2" />
                <span>No citations found in the text. Please try pasting a text with academic references.</span>
             </div>
          )}

          {/* 状态 4: 显示结果列表 */}
          {results && results.map((res, idx) => (
            <AuditCard key={idx} result={res} />
          ))}
        </div>
      </main>
    </div>
  );
}

// 审计卡片组件
function AuditCard({ result }: { result: AuditResult }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'REAL': return 'border-green-500 bg-green-50/50';
      case 'FAKE': return 'border-red-500 bg-red-50/50';
      case 'MISMATCH': return 'border-orange-500 bg-orange-50/50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const getIcon = (status: string) => {
    switch (status) {
      case 'REAL': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'FAKE': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'MISMATCH': return <AlertCircle className="w-5 h-5 text-orange-600" />;
      default: return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className={`p-5 rounded-lg border-l-4 shadow-sm bg-white transition-all ${getStatusColor(result.status)}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getIcon(result.status)}
          <span className="font-bold text-sm tracking-wide uppercase">{result.status}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 font-medium">
            {result.source}
          </span>
        </div>
        <div className="text-xs text-slate-400 font-mono">Confidence: {(result.confidence * 100).toFixed(0)}%</div>
      </div>

      <div className="mb-3 text-sm font-medium text-slate-800 italic border-l-2 border-slate-200 pl-3 py-1">
        "{result.citation_text.length > 100 ? result.citation_text.slice(0, 100) + '...' : result.citation_text}"
      </div>

      <div className="text-sm text-slate-600 leading-relaxed bg-white/50 p-3 rounded border border-slate-100">
        <ReactMarkdown>{result.message}</ReactMarkdown>
      </div>

      {result.metadata?.title && (
         <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
            <div className="flex items-center gap-2">
               <span className="font-semibold text-slate-700">Matched Source:</span> 
               {result.metadata.title} ({result.metadata.year})
            </div>
            {result.metadata.oa_url && (
                <a href={result.metadata.oa_url} target="_blank" className="text-indigo-600 hover:underline mt-1 inline-block">
                    View Full Text ↗
                </a>
            )}
         </div>
      )}
    </div>
  );
}