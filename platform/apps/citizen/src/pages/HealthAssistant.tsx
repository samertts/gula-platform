import { useState, useRef, useEffect } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { askGuideAssistant } from '../services/guideAssistant';
import type { ChatMessage } from '../types';

const quickQuestions = [
  'ما معنى نتيجة تحليل السكر المرتفعة؟',
  'هل يمكنني صرف الدواء بدون وصفة طبية؟',
  'كيف أحجز موعد استشارة عن بعد؟',
  'ما هي أعراض نقص فيتامين د؟',
  'متى يجب إجراء فحص السكر التالي؟',
];

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content: 'مرحباً! أنا مساعدك الصحي الذكي. يمكنني مساعدتك في فهم نتائج المختبر، معلومات عن الأدوية، التوصيات الصحية، والإجابة عن استفساراتك الطبية العامة. كيف يمكنني مساعدتك اليوم؟',
    timestamp: new Date().toISOString(),
    type: 'text',
  },
];

export function HealthAssistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(content: string) {
    if (!content.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      type: 'text',
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setError(null);
    setIsLoading(true);

    try {
      const result = await askGuideAssistant(content);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
        type: 'text',
        metadata: { model: result.model },
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (cause) {
      setMessages((prev) => prev.filter((message) => message.id !== userMessage.id));
      setInput(content);
      setError(cause instanceof Error ? cause.message : 'تعذر الوصول إلى المساعد حالياً.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="pb-24 flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 overflow-y-auto px-4 pt-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={cn('flex', msg.role === 'user' ? 'justify-start' : 'justify-end')}>
            <div className={cn(
              'max-w-[85%] rounded-2xl p-4',
              msg.role === 'user'
                ? 'bg-primary-50 dark:bg-primary-900/30 text-neutral-900 dark:text-neutral-50'
                : 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 shadow-sm',
            )}>
              <p className="text-sm leading-relaxed">{msg.content}</p>
              <p className="text-[9px] text-neutral-400 mt-2">
                {new Date(msg.timestamp).toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {error && (
          <div className="flex items-center justify-between gap-3 rounded-2xl border border-danger-200 bg-danger-50 p-3 text-xs text-danger-700 dark:border-danger-800 dark:bg-danger-900/20 dark:text-danger-300" role="alert">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => { setError(null); void handleSend(input); }}
              disabled={!input.trim() || isLoading}
              className="shrink-0 rounded-xl bg-white px-3 py-2 font-bold shadow-sm transition hover:bg-danger-100 active:scale-95 disabled:opacity-50 dark:bg-neutral-800"
            >
              إعادة المحاولة
            </button>
          </div>
        )}
        {isLoading && (
          <div className="flex justify-end">
            <div className="bg-white dark:bg-neutral-800 rounded-2xl p-4 border border-neutral-200 dark:border-neutral-700 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length <= 1 && (
        <div className="px-4 mt-4">
          <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-3">أسئلة سريعة</p>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSend(q)}
                className="px-4 py-2 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-2xl text-xs text-neutral-700 dark:text-neutral-300 hover:border-primary-300 dark:hover:border-primary-600 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="px-4 py-3 border-t border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder="اكتب سؤالك هنا..."
            className="flex-1 px-4 py-3 bg-neutral-100 dark:bg-neutral-800 rounded-2xl text-sm outline-none focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isLoading}
            className="w-12 h-12 bg-primary-500 text-white rounded-2xl flex items-center justify-center hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-[9px] text-neutral-400 mt-1.5 text-center">
          المعلومات المقدمة للأغراض التوعوية فقط وليست بديلاً عن الاستشارة الطبية
        </p>
      </div>
    </div>
  );
}
