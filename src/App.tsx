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

  // 1. 初始化与 URL 同步
  useEffect(() => {
    const syncWithUrl = () => {
      const params = new URLSearchParams(window.location.search);
      const note = params.get('note');
      console.log(`[WooToot-Debug] URL Note Parameter: ${note}`);
      setActiveNote(note);
    };

    window.addEventListener('popstate', syncWithUrl);
    syncWithUrl(); // 首次加载检查

    return () => window.removeEventListener('popstate', syncWithUrl);
  }, []);

  const openNote = (slug: string) => {
    console.log(`[WooToot-Debug] Opening Note: ${slug}`);
    const url = new URL(window.location.href);
    url.searchParams.set('note', slug);
    window.history.pushState({}, '', url);
    setActiveNote(slug);
    window.scrollTo(0, 0);
  };

  const closeNote = () => {
    console.log(`[WooToot-Debug] Closing Note`);
    const url = new URL(window.location.href);
    url.searchParams.delete('note');
    window.history.pushState({}, '', url);
    setActiveNote(null);
  };

  // 2. 物理渲染分支（绝对隔离）
  if (activeNote) {
    return (
      <div id="note-root" className="fixed inset-0 z-[10000] bg-background w-full h-full overflow-hidden">
        <NoteViewer slug={activeNote} onClose={closeNote} />
      </div>
    );
  }

  return (
    <div id="home-root" className="min-h-screen bg-background text-foreground">
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
