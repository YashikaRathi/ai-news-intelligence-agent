import React, { useState } from 'react';
import { Send, ExternalLink, Loader2, Sparkles, MessageCircle } from 'lucide-react';
import { askNews } from '../services/api';
import { ChatResponse } from '../types';

interface ChatBoxProps {
  storyId?: string;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ storyId }) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ q: string; a: ChatResponse }>>([]);

  const suggestedQuestions = [
    'What happened?',
    'Why is this important?',
    'What changed?',
    'Which sources reported this?',
  ];

  const handleSend = async (qToSend?: string) => {
    const targetQ = qToSend || question;
    if (!targetQ.trim() || loading) return;

    setLoading(true);
    try {
      const response = await askNews(storyId || null, targetQ.trim());
      setChatHistory((prev: Array<{ q: string; a: ChatResponse }>) => [...prev, { q: targetQ.trim(), a: response }]);
      setQuestion('');
    } catch {
      setChatHistory((prev: Array<{ q: string; a: ChatResponse }>) => [
        ...prev,
        {
          q: targetQ.trim(),
          a: {
            answer: "I couldn't find enough evidence in the available coverage to answer that reliably.",
            sources: [],
            is_demo: true,
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 space-y-4 shadow-sm font-sans">
      {/* Widget Header */}
      <div className="border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-[#EFF6FF] text-[#2563EB]">
            <Sparkles className="w-4 h-4 fill-[#2563EB]" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm text-[#0F172A]">
              Ask the News
            </h3>
            <p className="text-[11px] text-[#64748B] font-medium">
              Ask anything about this story...
            </p>
          </div>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider block">
          Suggested Questions:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {suggestedQuestions.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(sq)}
              disabled={loading}
              className="text-[11px] font-semibold text-[#0F172A] hover:text-[#2563EB] bg-[#F7FAFF] hover:bg-[#EFF6FF] border border-[#E2E8F0] px-2.5 py-1 rounded-full transition-all text-left"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Thread History */}
      <div className="space-y-4 max-h-[360px] overflow-y-auto no-scrollbar pr-1">
        {chatHistory.length === 0 ? (
          <div className="p-4 bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl text-center text-xs text-[#64748B] font-medium flex flex-col items-center gap-2">
            <MessageCircle className="w-5 h-5 text-[#2563EB]" />
            <span>Query the verified article evidence corpus for this story.</span>
          </div>
        ) : (
          chatHistory.map((item: { q: string; a: ChatResponse }, idx: number) => (
            <div key={idx} className="space-y-2 border-b border-[#E2E8F0] pb-3 last:border-0">
              {/* User Question */}
              <div className="bg-[#EFF6FF] rounded-xl p-3 text-xs text-[#0F172A] font-semibold border border-[#60A5FA]/30">
                <span className="font-bold text-[#2563EB] uppercase tracking-wider text-[10px] block mb-0.5">Q:</span>
                {item.q}
              </div>

              {/* AI Answer Card */}
              <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl p-3 text-xs text-[#0F172A] space-y-2">
                <span className="font-bold text-[#0F172A] uppercase tracking-wider text-[10px] block border-b border-[#E2E8F0] pb-1">
                  Evidence-Grounded Answer:
                </span>
                <p className="leading-relaxed text-[#0F172A] font-medium">{item.a.answer}</p>

                {item.a.sources && item.a.sources.length > 0 && (
                  <div className="pt-2 border-t border-[#E2E8F0] space-y-1.5">
                    <span className="text-[10px] font-bold text-[#2563EB] uppercase tracking-wider block">
                      Sources ({item.a.sources.length}):
                    </span>
                    <div className="space-y-1">
                      {item.a.sources.map((src: any, sIdx: number) => (
                        <div key={sIdx} className="bg-white border border-[#E2E8F0] p-2 rounded-lg flex items-center justify-between gap-2 text-[11px]">
                          <div className="truncate">
                            <span className="font-bold text-[#2563EB] uppercase text-[10px] block">
                              {src.source}
                            </span>
                            <span className="text-[#0F172A] font-semibold truncate block">
                              {src.title}
                            </span>
                          </div>
                          {src.url && src.url.startsWith('http') && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] font-bold text-[#2563EB] hover:underline shrink-0 bg-[#EFF6FF] px-2 py-1 rounded border border-[#60A5FA]/30"
                            >
                              <span>Read</span>
                              <ExternalLink className="w-3 h-3 text-[#2563EB]" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 pt-2 border-t border-[#E2E8F0]"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about this story..."
          disabled={loading}
          className="flex-1 px-3.5 py-2.5 bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl text-xs text-[#0F172A] placeholder-[#64748B] focus:outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-[#60A5FA]/20 transition font-medium"
        />
        <button
          type="submit"
          disabled={!question.trim() || loading}
          className="p-2.5 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50 text-white rounded-xl transition-colors shadow-sm shrink-0"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : <Send className="w-4 h-4 text-white" />}
        </button>
      </form>
    </div>
  );
};



