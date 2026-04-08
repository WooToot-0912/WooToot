import { Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { About } from './components/About';
import { Blog } from './components/Blog';
import { Projects } from './components/Projects';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';
import NoteViewer from './pages/NoteViewer';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground animate-in fade-in duration-500">
      <Routes>
        {/* 路由 1: 个人主页 */}
        <Route 
          path="/" 
          element={
            <>
              <Navigation />
              <main>
                <Hero />
                <About />
                <Blog />
                <Projects />
                <Contact />
              </main>
              <Footer />
            </>
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
