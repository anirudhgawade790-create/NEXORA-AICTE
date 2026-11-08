import { useEffect, useRef, useState } from 'react';
import { Bot, BookOpen, ChevronDown, LoaderCircle, Send, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiError, apiPost } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { useTheme } from '../../theme/ThemeContext';

type Topic = {
  keywords: string[];
  answer: string;
  label: string;
  path: string;
  roles?: string[];
};

type Message = {
  id: number;
  sender: 'assistant' | 'user';
  text: string;
  link?: { label: string; path: string };
};

const topics: Topic[] = [
  {
    keywords: [
      'application', 'applications', 'aplication', 'aplications', 'apply', 'submit',
      'new case', 'all case', 'all application', 'open all', 'case list', 'आवेदन',
    ],
    answer: 'Application dekhne ke liye Applications kholen. Institution account se New Application mein form bharke submit karein. Submit hone ke baad application list aur detail page par status aur timeline dekh sakte hain.',
    label: 'Open applications',
    path: '/applications',
  },
  {
    keywords: ['document', 'upload', 'file', 'pdf', 'evidence', 'दस्तावेज'],
    answer: 'Documents page par file upload karein. PDF, JPG/JPEG, PNG files (10 MB tak) supported hain. Upload ke baad status dekhein; OCR text sirf manual review mein madad karta hai, document verify ya approve nahi karta.',
    label: 'Open documents',
    path: '/documents',
  },
  {
    keywords: ['evc', 'committee', 'visit', 'inspection', 'finding'],
    answer: 'EVC page par scheduled visits dekhein. Authorized officer visit schedule karta hai; EVC/Committee account visit findings aur recommendation record karta hai. Ye demo workflow hai, official AICTE decision nahi.',
    label: 'Open EVC schedule',
    path: '/evc',
    roles: ['admin', 'regional_officer', 'bureau_officer', 'evc_committee'],
  },
  {
    keywords: ['compliance', 'undertaking', 'evidence', 'deadline', 'अनुपालन'],
    answer: 'Compliance page par undertakings aur due dates dekhein. Institution evidence submit kar sakta hai; authorized officer usse verify ya correction ke liye return kar sakta hai.',
    label: 'Open compliance',
    path: '/compliance',
  },
  {
    keywords: ['lease', 'expiry', 'renewal', 'ल lease'],
    answer: 'Lease Management page par lease expiry status dekhein aur jahan available ho wahan renewal evidence submit karein.',
    label: 'Open lease management',
    path: '/lease',
  },
  {
    keywords: ['role', 'permission', 'access', 'login', 'account', 'password', 'sign in', 'भूमिका'],
    answer: 'Available actions aapke account role par depend karte hain. Institution applications/evidence submit karta hai; officers workflow review karte hain; EVC committee findings record karti hai; admin users aur demo settings manage karta hai. Help page par full role guide hai.',
    label: 'View role guide',
    path: '/help',
  },
  {
    keywords: ['notification', 'alert', 'reminder', 'सूचना'],
    answer: 'Notifications page par aapke account ke alerts aur reminders milenge. Application ya record se related update dekhne ke liye notification ka link kholen.',
    label: 'Open notifications',
    path: '/notifications',
  },
  {
    keywords: ['report', 'analytics', 'csv', 'export'],
    answer: 'Reports page par apne access scope ke mutabik operational summaries dekhein aur available CSV reports download karein.',
    label: 'Open reports',
    path: '/reports',
  },
  {
    keywords: ['aicte', 'live data', 'public data', 'official data'],
    answer: 'AICTE Public Data page sirf tab records dikhata hai jab verified, authorized public data source configure ho. Application workflow records fictional demo data hain, live AICTE records nahi.',
    label: 'Open AICTE public data',
    path: '/aicte-data',
  },
  {
    keywords: ['security', 'safe', 'secure', 'privacy', 'real data'],
    answer: 'Ye prototype hai, production-certified system nahi. Sirf fictional demo records use karein. Real institutional data ke liye deployment security review, HTTPS, strong secrets, backups aur managed storage zaroori hain.',
    label: 'View safeguards',
    path: '/help',
  },
];

const quickQuestions = [
  'Application submit kaise karun?',
  'Document upload kaise hota hai?',
  'Mera role kya kar sakta hai?',
  'Kya ye live AICTE data hai?',
];

function findTopic(message: string): Topic | undefined {
  const normalized = message.toLocaleLowerCase().normalize('NFKC').replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim();
  return topics
    .map((topic) => ({
      topic,
      score: topic.keywords.reduce(
        (score, keyword) => score + (normalized.includes(keyword) ? keyword.length : 0),
        0,
      ),
    }))
    .filter((match) => match.score > 0)
    .sort((left, right) => right.score - left.score)[0]?.topic;
}

function getReply(message: string, role?: string): Omit<Message, 'id' | 'sender'> {
  const normalized = message.toLocaleLowerCase().normalize('NFKC').replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim();
  if (/^(hi+|hey+|hello+|helo+|hii+|namaste|namaskar|good morning|good afternoon|good evening)$/.test(normalized)) {
    return {
      text: 'Hello! Main NEXORA Agent hoon. Applications, documents, compliance, EVC ya account roles mein help chahiye?',
    };
  }

  const topic = findTopic(message);
  if (!topic) {
    return {
      text: 'Is sawaal ke liye general AI assistant chahiye. Backend par AI_CHAT_API_KEY configure karne ke baad main open-ended questions ka jawab de paunga. Tab tak Help page mein workspace guide dekh sakte hain.',
      link: { label: 'Open Help & system info', path: '/help' },
    };
  }
  if (topic.roles && role && !topic.roles.includes(role)) {
    return {
      text: `${topic.answer} Aapke current role ko EVC page access nahi hai; role ke mutabik permissions dekhne ke liye Help page kholen.`,
      link: { label: 'View role guide', path: '/help' },
    };
  }
  return { text: topic.answer, link: { label: topic.label, path: topic.path } };
}

export default function SupportAssistant() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [thinking, setThinking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      sender: 'assistant',
      text: 'Namaste! Main NEXORA ka help assistant hoon. Applications, documents, EVC, compliance aur account roles ke baare mein poochhein.',
    },
  ]);
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      inputRef.current?.focus();
    }
  }, [open, messages]);

  useEffect(() => {
    if (!open) return undefined;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [open]);

  async function sendMessage(text = draft) {
    const question = text.trim();
    if (!question || thinking) return;
    const conversation = [
      ...messages.slice(-10).map(({ sender, text: content }) => ({
        role: sender,
        content,
      })),
      { role: 'user', content: question },
    ];
    setMessages((current) => [...current, { id: nextId.current++, sender: 'user', text: question }]);
    setDraft('');
    setThinking(true);
    try {
      if (!user) {
        const isGreeting = /^(hi+|hey+|hello+|helo+|hii+|namaste|namaskar|good morning|good afternoon|good evening)$/i.test(question.trim());
        const localReply = getReply(question);
        const reply = findTopic(question) || isGreeting
          ? {
            ...localReply,
            link: localReply.link
              ? { label: 'Sign in to open workspace', path: '/login' }
              : undefined,
          }
          : {
            text: 'General AI help ke liye sign in karein. Main yahan NEXORA ke applications, documents aur workflow ke baare mein basic guidance de sakta hoon.',
            link: { label: 'Sign in', path: '/login' },
          };
        setMessages((current) => [...current, { id: nextId.current++, sender: 'assistant', ...reply }]);
        return;
      }

      const result = await apiPost<{ reply: string }>('/assistant/chat', { messages: conversation });
      setMessages((current) => [...current, {
        id: nextId.current++,
        sender: 'assistant',
        text: result.reply,
      }]);
    } catch (error) {
      let reply: Omit<Message, 'id' | 'sender'>;
      if (error instanceof ApiError && error.status === 503 && error.message.includes('AI_CHAT_API_KEY')) {
        const localReply = getReply(question, user?.role);
        reply = findTopic(question) || /^(hi+|hey+|hello+|helo+|hii+|namaste|namaskar|good morning|good afternoon|good evening)$/i.test(question.trim())
          ? {
            ...localReply,
            text: `General AI abhi configure nahi hai, isliye local guide se jawab de raha hoon. ${localReply.text}`,
          }
          : localReply;
      } else {
        reply = {
          text: error instanceof Error
            ? `Agent se connect nahi ho paaya: ${error.message}`
            : 'Agent se connect nahi ho paaya. Thodi der baad dobara try karein.',
        };
      }
      setMessages((current) => [...current, { id: nextId.current++, sender: 'assistant', ...reply }]);
    } finally {
      setThinking(false);
    }
  }

  return (
    <>
      {open && (
        <section
          aria-label="NEXORA Agent"
          className={`fixed bottom-[5.25rem] right-3 z-50 flex h-[min(72vh,600px)] w-[min(94vw,400px)] flex-col overflow-hidden rounded-[24px] border shadow-[0_24px_80px_-20px_rgba(15,35,75,0.42)] ring-1 ring-slate-900/5 sm:bottom-24 sm:right-6 ${isDark ? 'border-slate-700 bg-slate-900' : 'border-slate-200/80 bg-white'}`}
        >
          <header className="relative flex items-center justify-between overflow-hidden bg-gradient-to-br from-[#102A56] via-[#173b71] to-[#2563eb] px-4 py-4 text-white">
            <div className="pointer-events-none absolute -right-8 -top-12 h-32 w-32 rounded-full bg-blue-300/15 blur-2xl" />
            <div className="flex items-center gap-3">
              <span className="relative flex h-10 w-10 items-center justify-center rounded-2xl border border-white/20 bg-white/10 shadow-inner backdrop-blur">
                <Bot size={20} />
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#173b71] bg-emerald-400" />
              </span>
              <div className="relative">
                <h2 className="flex items-center gap-1.5 text-sm font-bold tracking-wide">NEXORA Agent <Sparkles size={13} className="text-blue-200" /></h2>
                <p className="mt-0.5 flex items-center gap-1.5 text-[10px] text-blue-100"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />AI workspace agent · Hinglish / English</p>
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close NEXORA Agent" className="relative rounded-xl border border-white/10 bg-white/5 p-2 text-blue-100 transition hover:bg-white/15 hover:text-white">
              <ChevronDown size={18} />
            </button>
          </header>

          <div className={`flex-1 space-y-3 overflow-y-auto p-4 ${isDark ? 'bg-slate-900' : 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/70 via-slate-50 to-slate-50'}`} aria-live="polite">
            {messages.length === 1 && (
              <div className={`mb-4 rounded-2xl border p-3.5 shadow-sm ${isDark ? 'border-slate-700 bg-slate-800' : 'border-blue-100/80 bg-white/90'}`}>
                <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-blue-600">Your workspace guide</p>
                <p className={`mt-1 text-xs leading-5 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>Ask about applications, documents, compliance, EVC, or what your role can do.</p>
              </div>
            )}
            {messages.map((message) => (
              <article key={message.id} className={`max-w-[90%] rounded-2xl px-3.5 py-3 text-xs leading-5 ${message.sender === 'user' ? 'ml-auto rounded-br-sm bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-sm' : `mr-auto rounded-bl-sm border shadow-sm ${isDark ? 'border-slate-700 bg-slate-800 text-slate-200' : 'border-slate-200/80 bg-white text-slate-700'}`}`}>
                <p>{message.text}</p>
                {message.link && (
                  <button
                    type="button"
                    onClick={() => navigate(message.link?.path ?? '/help')}
                    className={`mt-2 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 font-semibold transition ${isDark ? 'bg-blue-950/60 text-blue-300 hover:bg-blue-900/70' : 'bg-blue-50 text-brand-blue hover:bg-blue-100'}`}
                  >
                    <BookOpen size={13} />{message.link.label}
                  </button>
                )}
              </article>
            ))}
            {thinking && (
              <article aria-label="Agent is thinking" className={`mr-auto flex items-center gap-2 rounded-2xl rounded-bl-sm border px-3.5 py-3 text-xs ${isDark ? 'border-slate-700 bg-slate-800 text-slate-300' : 'border-slate-200/80 bg-white text-slate-600'}`}>
                <LoaderCircle size={14} className="animate-spin text-blue-500" /> Thinking…
              </article>
            )}
            {messages.length === 1 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {quickQuestions.map((question) => (
                  <button key={question} type="button" onClick={() => sendMessage(question)} className={`rounded-xl border px-3 py-2 text-left text-[10px] font-medium shadow-sm transition ${isDark ? 'border-slate-700 bg-slate-800 text-slate-200 hover:border-blue-700 hover:bg-slate-700 hover:text-blue-300' : 'border-blue-100 bg-white text-slate-600 hover:border-blue-300 hover:bg-blue-50 hover:text-brand-blue'}`}>
                    {question}
                  </button>
                ))}
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
            className={`flex items-center gap-2 border-t p-3.5 ${isDark ? 'border-slate-700 bg-slate-900' : 'border-slate-200/80 bg-white'}`}
          >
            <input
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Apna sawaal likhein..."
              aria-label="Ask the help assistant"
              maxLength={300}
              disabled={thinking}
              className={`h-11 min-w-0 flex-1 rounded-xl border px-3.5 text-xs outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 ${isDark ? 'border-slate-700 bg-slate-800 text-slate-100 focus:bg-slate-800' : 'border-slate-200 bg-slate-50 focus:bg-white'}`}
            />
            <button type="submit" disabled={!draft.trim() || thinking} aria-label="Send question" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0">
              {thinking ? <LoaderCircle size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
          <p className={`border-t px-3 py-2 text-center text-[9px] ${isDark ? 'border-slate-700 bg-slate-900 text-slate-400' : 'border-slate-100 bg-white text-slate-400'}`}>When enabled, chat is sent to OpenAI · Don’t share sensitive data</p>
        </section>
      )}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? 'Close NEXORA Agent' : 'Open NEXORA Agent'}
        aria-expanded={open}
        className="group fixed bottom-4 right-4 z-50 flex h-[58px] w-[58px] items-center justify-center rounded-full border border-white/20 bg-gradient-to-br from-[#102A56] via-[#173b71] to-[#2563eb] text-white shadow-[0_12px_35px_-10px_rgba(16,42,86,0.7)] ring-1 ring-slate-900/10 transition duration-200 hover:-translate-y-1 hover:shadow-[0_18px_40px_-10px_rgba(16,42,86,0.65)] focus:outline-none focus:ring-4 focus:ring-blue-200 sm:bottom-6 sm:right-6"
      >
        <span className={`agent-icon-float relative flex h-10 w-10 items-center justify-center rounded-full border border-white/15 bg-white/10 transition group-hover:bg-white/15 ${open ? 'agent-icon-static' : ''}`}>
          <Bot size={22} />
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-[#173b71] bg-emerald-400" />
        </span>
      </button>
    </>
  );
}
