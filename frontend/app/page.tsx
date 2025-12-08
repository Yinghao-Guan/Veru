'use client';

import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, CheckCircle, Search, AlertTriangle, Loader2, ShieldCheck, Database, Zap, Globe, History, Languages, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import HistoryDrawer, { HistoryItem, AuditResult } from '../components/HistoryDrawer';
import { translations, Language } from '../translations';

// 定义示例数据 (经典的三个案例)
const EXAMPLES = [
  // Case 1: FAKE (完全虚构)
  "Zhang, Wei & Miller, J. (2024). 'The Cognitive Impact of Blue Light on Deep Sea Jellyfish Navigation Patterns'. Journal of Marine Psychology. This study reveals that artificial blue light significantly disrupts the circadian rhythms of deep-sea jellyfish.",

  // Case 2: MISMATCH (张冠李戴 - ResNet 煮面条)
  "'Deep Residual Learning for Image Recognition' by Kaiming He. This paper proposes a new method for cooking spaghetti using neural networks.",

  // Case 3: REAL (真实且年份有争议，展示纠错能力)
  "Devlin et al., 2018 – “BERT: Pre-training of Deep Bidirectional Transformers”\nPopularized transformer-based language models."
];

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

function AuditCard({ result, t }: { result: AuditResult, t: typeof translations.en }) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'REAL': return { color: 'border-emerald-500 bg-emerald-50/30', icon: <CheckCircle className="w-5 h-5 text-emerald-600" />, text: 'text-emerald-700' };
      case 'FAKE': return { color: 'border-rose-500 bg-rose-50/30', icon: <AlertTriangle className="w-5 h-5 text-rose-600" />, text: 'text-rose-700' };
      case 'MISMATCH': return { color: 'border-amber-500 bg-amber-50/30', icon: <AlertCircle className="w-5 h-5 text-amber-600" />, text: 'text-amber-700' };
      case 'MINOR_ERROR': return { color: 'border-cyan-500 bg-cyan-50/30', icon: <AlertCircle className="w-5 h-5 text-cyan-600" />, text: 'text-cyan-700' };
      default: return { color: 'border-slate-300 bg-slate-50', icon: <AlertCircle className="w-5 h-5 text-slate-500" />, text: 'text-slate-600' };
    }
  };
  const config = getStatusConfig(result.status);

  const localizedStatus = t.status[result.status as keyof typeof t.status] || result.status;

  return (
    <div className={`p-5 rounded-xl border-l-4 shadow-sm bg-white transition-all hover:shadow-md ${config.color}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {config.icon}
          <span className={`font-bold text-sm tracking-wide uppercase ${config.text}`}>{localizedStatus}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-100 text-slate-500 font-medium uppercase tracking-wider">
            {result.source}
          </span>
        </div>
        {result.confidence > 0 && (
            <div className="text-xs text-slate-400 font-mono" title="AI Confidence Score">
                {Math.round(result.confidence * 100)}% {t.confidence}
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
            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">{t.sourceMatch}</span>
            <div className="text-slate-700 font-medium">
               {result.metadata.title} ({result.metadata.year})
            </div>
            {result.metadata.oa_url && (
                <a href={result.metadata.oa_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 hover:underline mt-1 inline-flex items-center transition-colors">
                    {t.viewFullText} <span className="ml-1">→</span>
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

  const [lang, setLang] = useState<Language>('en');
  const t = translations[lang];

  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // 示例索引，用于轮播
  const [exampleIndex, setExampleIndex] = useState(0);

  useEffect(() => {
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) {
      setLang('zh');
    }
  }, []);

  const toggleLanguage = () => {
    setLang(prev => prev === 'en' ? 'zh' : 'en');
  };

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

  const saveToHistory = (text: string, res: AuditResult[]) => {
    const newItem: HistoryItem = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      inputText: text,
      results: res
    };
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

  // 处理点击“试一试”
  const handleTryExample = () => {
    const example = EXAMPLES[exampleIndex];
    setInputText(example);
    // 轮播索引 (0 -> 1 -> 2 -> 0)
    setExampleIndex((prev) => (prev + 1) % EXAMPLES.length);
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

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-slate-800 font-sans flex flex-col">
      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        history={history}
        onClear={clearHistory}
        t={t}
        onSelect={(item) => {
            setInputText(item.inputText);
            setResults(item.results);
        }}
      />

      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center cursor-pointer" onClick={() => window.location.reload()}>
            <VeruLogo />
            <span className="text-xl font-bold tracking-tight text-slate-900">Veru</span>
          </div>
          <nav className="flex items-center space-x-3">
            <a href="#features" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors hidden sm:block">
              {t.howItWorks}
            </a>
            <div className="text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full border border-blue-100 hidden sm:block">
              {t.previewBadge}
            </div>

            <button
              onClick={toggleLanguage}
              className="p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors flex items-center gap-1 font-medium text-sm"
              title="Switch Language"
            >
              <Languages className="w-4 h-4" />
              <span>{lang === 'en' ? 'EN' : '中文'}</span>
            </button>

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

      <main className="flex-1 w-full bg-gradient-to-b from-[#F8F9FA] to-white">
        <div className="max-w-7xl mx-auto px-6 py-10 lg:py-14">

          <div className="text-center mb-10 max-w-2xl mx-auto">
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">
              {t.heroTitle} <span className="text-blue-600">{t.heroTitleHighlight}</span>
            </h1>
            <p className="text-slate-500 text-lg">
              {t.heroDesc}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 h-[600px] lg:h-[700px]">
            {/* Left: Input */}
            <div className="flex flex-col h-full">
              <div className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-1 flex-1 flex flex-col transition-all focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-400 overflow-hidden">

                {/* 🔴 Header with Try Example Button */}
                <div className="bg-slate-50/50 border-b border-slate-100 px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                            <Search className="w-3.5 h-3.5 mr-2 text-blue-500" />
                            {t.inputLabel}
                        </label>
                    </div>

                    {/* Try Example 按钮 */}
                    <button
                        onClick={handleTryExample}
                        className="text-xs font-bold text-blue-600 bg-white hover:bg-blue-50 border border-blue-100 px-3 py-1.5 rounded-lg flex items-center transition-colors shadow-sm"
                    >
                        <Sparkles className="w-3 h-3 mr-1.5 text-amber-500" />
                        {t.tryExampleBtn}
                    </button>
                </div>

                <textarea
                  className="flex-1 w-full p-6 bg-white outline-none resize-none font-mono text-sm leading-7 text-slate-700 placeholder:text-slate-300"
                  placeholder={t.placeholder}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                />

                <div className="p-4 bg-white border-t border-slate-50 flex justify-between items-center">
                  <span className={`text-xs ${inputText.length > 5000 ? 'text-rose-500 font-bold' : 'text-slate-400'}`}>
                    {inputText.length} / 5,000 {t.charCount}
                  </span>
                  <button
                    onClick={handleAudit}
                    // 如果超限，禁用按钮
                    disabled={loading || !inputText || inputText.length > 5000}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all flex items-center disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-xl active:scale-95"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        {t.verifyingBtn}
                      </>
                    ) : (
                      t.checkBtn
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
                        {t.reportLabel}
                        </label>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {!results && !loading && (
                            <div className="h-full flex flex-col items-center justify-center text-slate-400 p-8 text-center">
                            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm mb-6 border border-slate-100">
                                <BookOpen className="w-10 h-10 text-blue-200" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-600 mb-2">{t.readyTitle}</h3>
                            <p className="text-sm text-slate-400 max-w-xs mx-auto">
                                {t.readyDesc}
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
                                    <p className="text-slate-600 font-medium">{t.processingTitle}</p>
                                    <p className="text-slate-400 text-xs mt-2">{t.processingDesc}</p>
                                </div>
                            </div>
                            </div>
                        )}

                        {results && results.length === 0 && (
                            <div className="p-4 rounded-xl bg-orange-50 border border-orange-100 text-orange-800 flex items-start">
                                <AlertTriangle className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-semibold text-sm">{t.noCitationsTitle}</p>
                                    <p className="text-xs mt-1 text-orange-700/80">{t.noCitationsDesc}</p>
                                </div>
                            </div>
                        )}

                        {results && results.map((res, idx) => (
                            <AuditCard key={idx} result={res} t={t} />
                        ))}
                    </div>
                </div>
            </div>

          </div>
        </div>
      </main>

      <section id="features" className="bg-white border-t border-slate-200 py-20">
        <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
                <h2 className="text-3xl font-bold text-slate-900 mb-4">{t.whyTitle}</h2>
                <p className="text-slate-500 max-w-2xl mx-auto">{t.whyDesc}</p>
            </div>

            <div className="grid md:grid-cols-3 gap-10">
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mb-6 text-blue-600">
                        <Database className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">{t.feat1Title}</h3>
                    <p className="text-slate-500 leading-relaxed" dangerouslySetInnerHTML={{ __html: t.feat1Desc }} />
                </div>
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mb-6 text-emerald-600">
                        <ShieldCheck className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">{t.feat2Title}</h3>
                    <p className="text-slate-500 leading-relaxed" dangerouslySetInnerHTML={{ __html: t.feat2Desc }} />
                </div>
                <div className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 transition-colors">
                    <div className="w-14 h-14 bg-amber-100 rounded-2xl flex items-center justify-center mb-6 text-amber-600">
                        <Globe className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-3">{t.feat3Title}</h3>
                    <p className="text-slate-500 leading-relaxed" dangerouslySetInnerHTML={{ __html: t.feat3Desc }} />
                </div>
            </div>
        </div>
      </section>

      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
                <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-md flex items-center justify-center text-white font-bold text-xs">V</div>
                <span className="font-bold text-slate-100 tracking-tight">Veru</span>
            </div>
            <div className="text-sm">
                &copy; {new Date().getFullYear()} Veru Audit. {t.rightsReserved}
            </div>
        </div>
      </footer>
    </div>
  );
}