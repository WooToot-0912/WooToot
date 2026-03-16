import React from 'react';
import { Navigation } from './components/Navigation';

// This is required to satisfy strict tsconfig where React must be imported but might be unused in TSX
void React;

import { Hero } from './components/Hero';
import { About } from './components/About';
import { Blog } from './components/Blog';
import { Projects } from './components/Projects';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />
      <main>
        <Hero />
        <About />
        <Blog />
        <Projects />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}