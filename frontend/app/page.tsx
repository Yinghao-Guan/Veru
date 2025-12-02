'use client';

import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, CheckCircle, Search, AlertTriangle, Loader2, ShieldCheck, Database, Zap, Globe, History, Clock, Github } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import HistoryDrawer, { HistoryItem, AuditResult } from '../components/HistoryDrawer';

// Logo 组件
function VeruLogo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" className="w-8 h-8 mr-2">
      <defs>
        <linearGradient id="logo_grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#2563EB', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#06B6D4', stopOpacity: 1 }} />
        </linearGradient>
      </defs>
      <rect width="512" height="512" rx="128" fill="url(#logo_grad)" />
      <path d="M140 200 L210 340 L380 140" stroke="white" strokeWidth="64" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function AuditCard({ result }: { result: AuditResult }) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'REAL':
        return { color: 'border-emerald-500 bg-emerald-50/30', icon: <CheckCircle className="w-5 h-5 text-emerald-600" />, text: 'text-emerald-700' };
      case 'FAKE':
        return { color: 'border-rose-500 bg-rose-50/30', icon: <AlertTriangle className="w-5 h-5 text-rose-600" />, text: 'text-rose-700' };
      case 'MISMATCH':
        return { color: 'border-amber-500 bg-amber-50/30', icon: <AlertCircle className="w-5 h-5 text-amber-600" />, text: 'text-amber-700' };
      case 'MINOR_ERROR':
        return { color: 'border-cyan-500 bg-cyan-50/30', icon: <AlertCircle className="w-5 h-5 text-cyan-600" />, text: 'text-cyan-700' };
      default:
        return { color: 'border-slate-300 bg-slate-50', icon: <AlertCircle className="w-5 h-5 text-slate-500" />, text: 'text-slate-600' };
    }
  };
  // ... 后面的代码不变
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
                <a href={result.metadata.oa_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 hover:underline mt-1 inline-flex items-center transition-colors">
                    View Full Text <span className="ml-1">→</span>
                </a>
            )}
         </div>
      )}
    </div>
  );
}

export default function Home() {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AuditResult[] | null>(null);

  // 历史记录相关状态
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // 加载历史记录
  useEffect(() => {
    const saved = localStorage.getItem('veru_history');
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load history');
      }
    }
  }, []);

  // 保存历史记录的函数
  const saveToHistory = (text: string, res: AuditResult[]) => {
    const newItem: HistoryItem = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      inputText: text,
      results: res
    };

    // 最多保存 20 条，新的在前
    const newHistory = [newItem, ...history].slice(0, 20);
    setHistory(newHistory);
    localStorage.setItem('veru_history', JSON.stringify(newHistory));
  };

  const clearHistory = () => {
    if (confirm('Are you sure you want to clear all history?')) {
        setHistory([]);
        localStorage.removeItem('veru_history');
    }
  };

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

      // ✅ 成功获取结果后，保存到历史
      if (data && data.length > 0) {
        saveToHistory(inputText, data);
      }

    } catch (error) {
      console.error('API Error:', error);
      alert('Unable to connect to the audit server. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // 定义结构化数据
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    'name': 'Veru',
    'applicationCategory': 'EducationalApplication',
    'operatingSystem': 'Web',
    'offers': {
      '@type': 'Offer',
      'price': '0',
      'priceCurrency': 'USD'
    },
    'description': 'An AI hallucination detection tool that verifies academic citations generated by LLMs against real databases like OpenAlex.',
    'aggregateRating': {
      '@type': 'AggregateRating',
      'ratingValue': '4.8',
      'ratingCount': '24'
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-slate-800 font-sans flex flex-col">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* 历史记录侧边栏 */}
      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        history={history}
        onClear={clearHistory}
        onSelect={(item) => {
            setInputText(item.inputText);
            setResults(item.results);
        }}
      />

      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center cursor-pointer" onClick={() => window.location.reload()}>
            <VeruLogo />
            <span className="text-xl font-bold tracking-tight text-slate-900">Veru</span>
          </div>
          <nav className="flex items-center space-x-4">
            <div className="text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full border border-blue-100 hidden sm:block">
              Free Research Preview
            </div>
            {/* History Button */}
            <button
                onClick={() => setHistoryOpen(true)}
                className="p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors relative"
                title="View History"
            >
                <History className="w-5 h-5" />
                {history.length > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white"></span>
                )}
            </button>
          </nav>
        </div>
      </header>

      {/* Main Tool Section */}
      <main className="flex-1 w-full bg-gradient-to-b from-[#F8F9FA] to-white">
        <div className="max-w-7xl mx-auto px-6 py-10 lg:py-14">

          <div className="text-center mb-10 max-w-2xl mx-auto">
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">
              Verify Academic Citations <span className="text-blue-600">Instantly</span>
            </h1>
            <p className="text-slate-500 text-lg">
              Don't let AI hallucinations ruin your research. Paste your text below to audit citations against real academic databases.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 h-[600px] lg:h-[700px]">
            {/* Left: Input */}
            <div className="flex flex-col h-full">
              <div className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-1 flex-1 flex flex-col transition-all focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-400 overflow-hidden">
                <div className="bg-slate-50/50 border-b border-slate-100 px-4 py-3 flex items-center justify-between">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                    <Search className="w-3.5 h-3.5 mr-2 text-blue-500" />
                    Input Source
                    </label>
                    <span className="text-[10px] text-slate-400">Supports ChatGPT, Claude, Perplexity</span>
                </div>
                <textarea
                  className="flex-1 w-full p-6 bg-white outline-none resize-none font-mono text-sm leading-7 text-slate-700 placeholder:text-slate-300"
                  placeholder="Paste text here...
Example: 'As discussed by Ekman (1999) in his study on basic emotions...'"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                />
                <div className="p-4 bg-white border-t border-slate-50 flex justify-between items-center">
                  <span className="text-xs text-slate-400">
                    {inputText.length} characters
                  </span>
                  <button
                    onClick={handleAudit}
                    disabled={loading || !inputText}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all flex items-center disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-xl active:scale-95"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Auditing...
                      </>
                    ) : (
                      'Check Citations'
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Results */}
            <div className="flex flex-col h-full overflow-hidden">
                <div className="bg-slate-50 rounded-2xl border border-slate-200 flex-1 flex flex-col overflow-hidden relative">
                    <div className="bg-white/80 backdrop-blur border-b border-slate-200 px-4 py-3 flex items-center">
                        <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                        <ShieldCheck className="w-3.5 h-3.5 mr-2 text-emerald-500" />
                        Audit Report
                        </label>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {!results && !loading && (
                            <div className="h-full flex flex-col items-center justify-center text-slate-400 p-8 text-center">
                            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm mb-6 border border-slate-100">
                                <BookOpen className="w-10 h-10 text-blue-200" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-600 mb-2">Ready to verify</h3>
                            <p className="text-sm text-slate-400 max-w-xs mx-auto">
                                Paste any academic text on the left. Veru will cross-reference citations against 250M+ real papers.
                            </p>
                            </div>
                        )}

                        {loading && (
                            <div className="h-full flex flex-col items-center justify-center">
                            <div className="text-center space-y-6">
                                <div className="relative mx-auto w-16 h-16">
                                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full animate-spin border-t-blue-600"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-8 h-8 bg-blue-50 rounded-full"></div>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-slate-600 font-medium">Running forensic analysis...</p>
                                    <p className="text-slate-400 text-xs mt-2">Connecting to OpenAlex & Google Search</p>
                                </div>
                            </div>
                            </div>
                        )}

                        {results && results.length === 0 && (
                            <div className="p-4 rounded-xl bg-orange-50 border border-orange-100 text-orange-800 flex items-start">
                                <AlertTriangle className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-semibold text-sm">No citations detected</p>
                                    <p className="text-xs mt-1 text-orange-700/80">Try pasting a text that contains references like "Author (Year)" or "Title by Author".</p>
                                </div>
                            </div>
                        )}

                        {results && results.map((res, idx) => (
                            <AuditCard key={idx} result={res} />
                        ))}
                    </div>
                </div>
            </div>
          </div>
        </div>
      </main>

      {/* Feature Section & Footer (保持不变) */}
      <section id="features" className="bg-white border-t border-slate-200 py-20">
        <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
                <h2 className="text-3xl font-bold text-slate-900 mb-4">Why use Veru?</h2>
                <p className="text-slate-500 max-w-2xl mx-auto">ChatGPT and other LLMs often hallucinate citations. Veru acts as your forensic auditor.</p>
            </div>
            <div className="grid md:grid-cols-3 gap-10">
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mb-6 text-blue-600">
                        <Database className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">Real Database Check</h3>
                    <p className="text-slate-500 leading-relaxed">
                        We cross-reference every citation against <strong>OpenAlex</strong>, a massive database of 250 million+ academic works.
                    </p>
                </div>
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mb-6 text-emerald-600">
                        <ShieldCheck className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">Anti-Hallucination</h3>
                    <p className="text-slate-500 leading-relaxed">
                        Our "Auditor" AI compares the user's claim against the <strong>actual abstract</strong> to detect mismatched or fake summaries.
                    </p>
                </div>
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-amber-100 rounded-2xl flex items-center justify-center mb-6 text-amber-600">
                        <Globe className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">Google Grounding</h3>
                    <p className="text-slate-500 leading-relaxed">
                        If a paper isn't in the database, we use <strong>Google Search</strong> to perform a final forensic sweep of the web.
                    </p>
                </div>
            </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center">

            {/* 左侧：Logo */}
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
                <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-md flex items-center justify-center text-white font-bold text-xs">V</div>
                <span className="font-bold text-slate-100 tracking-tight">Veru</span>
            </div>

            {/* 右侧：版权信息 + GitHub 链接 */}
            <div className="flex items-center space-x-6">
                <a
                  href="https://github.com/Yinghao-Guan/Veru"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                  aria-label="View Source on GitHub"
                >
                    <Github className="w-5 h-5" />
                </a>
                <div className="text-sm border-l border-slate-700 pl-6 ml-2">
                    &copy; {new Date().getFullYear()} Veru Audit.
                </div>
            </div>

        </div>
      </footer>
    </div>
  );
}