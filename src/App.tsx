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
    // 初始化检查
    const params = new URLSearchParams(window.location.search);
    setActiveNote(params.get('note'));
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const openNote = (slug: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('note', slug);
    window.history.pushState({}, '', url);
    setActiveNote(slug);
  };

  const closeNote = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete('note');
    window.history.pushState({}, '', url);
    setActiveNote(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* 如果没有打开笔记，显示完整主页 */}
      <div className={activeNote ? 'hidden' : 'block'}>
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

      {/* 如果打开了笔记，显示安全阅读层 */}
      {activeNote && (
        <div className="fixed inset-0 z-[9999] bg-background overflow-y-auto">
          <NoteViewer slug={activeNote} onClose={closeNote} />
        </div>
      )}
    </div>
  );
}
