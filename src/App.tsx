import { useState, useEffect } from 'react';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { About } from './components/About';
import { Blog } from './components/Blog';
import { Projects } from './components/Projects';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';
import NoteViewer from './pages/NoteViewer';

export default function App() {
  const [activeNote, setActiveNote] = useState<string | null>(null);

  // 监听 URL 变化，支持前进后退关闭笔记
  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      setActiveNote(params.get('note'));
    };
    window.addEventListener('popstate', handlePopState);
    
    const params = new URLSearchParams(window.location.search);
    setActiveNote(params.get('note'));
    
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const openNote = (slug: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('note', slug);
    window.history.pushState({}, '', url);
    setActiveNote(slug);
    // 强制滚动到顶部
    window.scrollTo(0, 0);
  };

  const closeNote = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete('note');
    window.history.pushState({}, '', url);
    setActiveNote(null);
  };

  // 核心逻辑：物理切换主页与笔记页
  if (activeNote) {
    return (
      <div className="min-h-screen bg-slate-900">
        <NoteViewer slug={activeNote} onClose={closeNote} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground animate-in fade-in duration-500">
      <Navigation />
      <main>
        <Hero />
        <About />
        <Blog onOpenNote={openNote} />
        <Projects />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
