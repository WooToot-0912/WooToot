import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { About } from './components/About';
import { Blog } from './components/Blog';
import { Projects } from './components/Projects';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';
import NoteViewer from './pages/NoteViewer';

function HomePage() {
  return (
    <>
      <Hero />
      <About />
      <Blog />
      <Projects />
      <Contact />
    </>
  );
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground">
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/note/:slug" element={<NoteViewer />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}
