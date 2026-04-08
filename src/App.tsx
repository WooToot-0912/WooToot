import { useState } from 'react';
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

  const openNote = (slug: string) => {
    console.log(`[WooToot-Final] Triggering Note: ${slug}`);
    setActiveNote(slug);
    // 强制锁定滚动条，防止主页在下面滚动
    document.body.style.overflow = 'hidden';
  };

  const closeNote = () => {
    console.log(`[WooToot-Final] Closing Note`);
    setActiveNote(null);
    // 恢复滚动条
    document.body.style.overflow = 'unset';
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative text-white">
      {/* 1. 主页展示逻辑 */}
      {!activeNote && (
        <div className="animate-in fade-in duration-500">
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
      )}

      {/* 2. 笔记页展示逻辑 (最高优先级全屏覆盖) */}
      {activeNote && (
        <div className="fixed inset-0 z-[99999] bg-slate-900 w-full h-full overflow-hidden">
          <NoteViewer slug={activeNote} onClose={closeNote} />
        </div>
      )}
    </div>
  );
}
