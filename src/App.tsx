import { Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { About } from './components/About';
import { Blog } from './components/Blog';
import { Projects } from './components/Projects';
import { LearningNotes } from './components/LearningNotes';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';
import NoteViewer from './pages/NoteViewer';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground animate-in fade-in duration-500">
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] animate-blob" />
        <div className="absolute top-[20%] right-[-5%] w-[35%] h-[35%] bg-purple-600/10 rounded-full blur-[120px] animate-blob animation-delay-2000" />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px] animate-blob animation-delay-4000" />
      </div>

      <Routes>
        {/* 路由 1: 个人主页 */}
        <Route
          path="/"
          element={
            <div className="relative z-10">
              <Navigation />
              <main>
                <Hero />
                <About />
                <Projects />
                <LearningNotes />
                <Blog />
                <Contact />
              </main>
              <Footer />
            </div>
          }
        />

        {/* 路由 2: 安全笔记阅读器 (绝对物理隔离) */}
        <Route
          path="/note/:slug"
          element={<NoteViewer />}
        />
      </Routes>
    </div>
  );
}
