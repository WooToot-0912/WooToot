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
    setActiveNote(slug);
    // 固定身体防止滚动
    document.body.style.overflow = 'hidden';
  };

  const closeNote = () => {
    setActiveNote(null);
    document.body.style.overflow = 'unset';
  };

  // 物理互斥渲染逻辑
  return (
    <div className="min-h-screen bg-background text-foreground">
      {activeNote ? (
        /* 笔记视图：使用最顶层固定定位，背景加深 */
        <div className="fixed inset-0 z-[99999] bg-slate-950 overflow-hidden">
          <NoteViewer slug={activeNote} onClose={closeNote} />
        </div>
      ) : (
        /* 主页视图：完全正常的各模块渲染 */
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
    </div>
  );
}
