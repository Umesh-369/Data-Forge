'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { sendDatasetChatMessage } from '@/lib/api';
import { Sparkles, Send, Code2, AlertCircle, RefreshCw, ChevronDown, ChevronUp, Bot, User } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  trace?: string;
  showTrace?: boolean;
}

export default function ChatPanel() {
  const { currentDataset, currentVersionId } = useAppStore();
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'initial-welcome',
      sender: 'bot',
      text: "Hey there, data wrangler! I'm your Data Chatbot. Ask me anything about your current dataset version and I'll compute exact figures in the sandbox for you.",
    }
  ]);

  const starterSuggestions = [
    "Any missing values in dataset?",
    "Show me the weirdest column here"
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleTrace = (id: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === id ? { ...msg, showTrace: !msg.showTrace } : msg
      )
    );
  };

  const handleSendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || !currentDataset || isSubmitting) return;

    const userMsgId = `user-${Date.now()}`;
    const newMessages: ChatMessage[] = [
      ...messages,
      { id: userMsgId, sender: 'user', text: trimmed }
    ];

    setMessages(newMessages);
    setPrompt('');
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      // Build conversation history format
      const history = newMessages.map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

      const activeVersionId = currentVersionId || currentDataset.current_version_id;
      const res = await sendDatasetChatMessage(activeVersionId, trimmed, history);

      const botMsgId = `bot-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          sender: 'bot',
          text: res.answer,
          trace: res.computation_trace,
          showTrace: false
        }
      ]);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to communicate with Data Chatbot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-200 flex flex-col h-full overflow-hidden shadow-sm">
      {/* Panel Header - 1. Title & Subtitle */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-brand-gradient rounded-xl text-white shadow-md shadow-brand-500/20 shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Data Chatbot</h3>
            <p className="text-[11px] text-slate-500 font-medium">Ask anything about your dataset</p>
          </div>
        </div>
      </div>

      {/* Main Chat Thread - 3. Scrollable Message List */}
      <div className="p-4 flex-1 overflow-y-auto space-y-4 min-h-[380px] max-h-[500px]">
        {errorMsg && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-start gap-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-2.5 ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.sender === 'bot' && (
              <div className="w-7 h-7 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-600 shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}

            <div className="space-y-2 max-w-[85%]">
              <div
                className={`p-3.5 text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-brand-500 text-white rounded-2xl rounded-tr-xs shadow-md font-semibold'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-2xl rounded-tl-xs shadow-sm'
                }`}
              >
                {msg.text}
              </div>

              {/* 3 & 6. Show computation toggle for bot replies */}
              {msg.sender === 'bot' && msg.trace && (
                <div className="pl-1">
                  <button
                    onClick={() => toggleTrace(msg.id)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 hover:border-brand-500/40 text-[10px] font-mono text-brand-700 hover:text-brand-800 transition-all cursor-pointer shadow-sm"
                  >
                    <Code2 className="w-3 h-3 text-brand-600" />
                    <span>{msg.showTrace ? 'Hide computation' : 'Show computation'}</span>
                    {msg.showTrace ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>

                  {msg.showTrace && (
                    <div className="mt-2 p-3 bg-slate-900 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-100 space-y-1 shadow-inner animate-in fade-in zoom-in-95 duration-150">
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider font-sans font-bold flex items-center gap-1 border-b border-slate-800 pb-1 mb-1">
                        <Code2 className="w-3 h-3 text-brand-400" /> Exact Sandbox Pandas Query:
                      </div>
                      <pre className="whitespace-pre-wrap break-all text-emerald-300">
                        {msg.trace}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-7 h-7 rounded-xl bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-700 shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {isSubmitting && (
          <div className="flex items-center gap-2 text-xs text-brand-300 bg-brand-500/10 p-3 rounded-2xl border border-brand-400/20 w-fit animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand-400" />
            <span>Computing pandas sandbox query...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer Area - 4. Starter Suggestions & 5. Input Bar */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/80 space-y-2.5">
        {/* 4. Starter Suggestions */}
        <div className="flex flex-wrap items-center gap-1.5 px-1">
          {starterSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => handleSendMessage(suggestion)}
              disabled={isSubmitting || !currentDataset}
              className="px-2.5 py-1 bg-white hover:bg-brand-500/10 border border-slate-200 hover:border-brand-500/40 rounded-full text-[11px] text-brand-700 font-semibold transition-all text-left disabled:opacity-50 cursor-pointer shadow-sm"
            >
              "{suggestion}"
            </button>
          ))}
        </div>

        {/* 5. Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(prompt);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder={currentDataset ? "Ask about your data..." : "Select a dataset to chat..."}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={!currentDataset || isSubmitting}
            className="flex-1 px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-brand-500 disabled:opacity-40 font-medium shadow-sm"
          />
          <button
            type="submit"
            disabled={!currentDataset || !prompt.trim() || isSubmitting}
            className="p-2.5 bg-brand-gradient hover:opacity-90 text-white rounded-xl disabled:opacity-40 transition-all flex items-center justify-center shadow-lg shadow-brand-500/20 cursor-pointer"
          >
            {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
      </div>
    </div>
  );
}
