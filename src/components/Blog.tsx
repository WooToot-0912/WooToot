import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Calendar, Clock, ArrowRight, MessageCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const blogPosts = [
  {
    id: 1,
    title: 'Building Modern Web Applications with React and TypeScript',
    excerpt: 'Learn how to build type-safe, scalable web applications using React and TypeScript. Best practices, patterns, and tips.',
    date: '2024-03-15',
    readTime: '8 min read',
    category: 'Development',
    slug: 'building-modern-web-applications',
    content: `
## Introduction

React and TypeScript have become the gold standard for building modern web applications. In this post, I'll share my experience and best practices.

## Why TypeScript?

TypeScript adds static type checking to JavaScript, catching errors at compile time rather than runtime.

## Best Practices

1. **Strict Mode**: Always enable strict mode in your tsconfig.json
2. **Component Props**: Define interfaces for all component props
3. **Generic Components**: Use generics for reusable components

## Conclusion

TypeScript is an invaluable tool for React development.
    `,
  },
  {
    id: 2,
    title: 'The Future of CSS: Tailwind and Beyond',
    excerpt: 'Exploring the evolution of CSS frameworks and why utility-first CSS is taking over the web development world.',
    date: '2024-03-10',
    readTime: '6 min read',
    category: 'CSS',
    slug: 'future-of-css-tailwind',
    content: `
## The Rise of Utility-First CSS

Tailwind CSS has revolutionized how we write styles. No more switching between HTML and CSS files.

## Benefits

- **Rapid Development**: Build interfaces faster
- **Consistency**: Standardized design system
- **Small Bundle Size**: Purge unused styles

## What's Next?

The future looks bright for CSS-in-JS and utility-first approaches.
    `,
  },
  {
    id: 3,
    title: 'Mastering Framer Motion for React Animations',
    excerpt: 'Create stunning, performant animations in React with Framer Motion. From basics to advanced techniques.',
    date: '2024-03-05',
    readTime: '10 min read',
    category: 'Animation',
    slug: 'mastering-framer-motion',
    content: `
## Getting Started

Framer Motion is a production-ready motion library for React.

## Key Concepts

- **motion components**: Enhanced HTML elements
- **AnimatePresence**: Handle entering/exiting animations
- **useAnimation**: Programmatic control

## Advanced Techniques

Learn about layout animations, shared layout animations, and more.
    `,
  },
];

export function Blog() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [selectedPost, setSelectedPost] = useState<typeof blogPosts[0] | null>(null);

  return (
    <section id="blog" className="py-24 md:py-32 bg-secondary/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 50 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          {/* Section Header */}
          <div className="text-center mb-16">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.2 }}
              className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4"
            >
              {t('blog.title')}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-lg max-w-2xl mx-auto"
            >
              {t('blog.subtitle')}
            </motion.p>
          </div>

          {/* Blog Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {blogPosts.map((post, index) => (
              <motion.article
                key={post.id}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ y: -10 }}
                className="group bg-card rounded-2xl overflow-hidden border border-border hover:border-primary/50 transition-all cursor-pointer"
                onClick={() => setSelectedPost(post)}
              >
                <div className="aspect-video bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-4xl font-bold text-foreground/20">{post.category}</span>
                  </div>
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 text-xs font-medium rounded-full bg-background/80 backdrop-blur-sm">
                      {post.category}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{post.date}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{post.readTime}</span>
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-muted-foreground mb-4 line-clamp-3">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center text-primary font-medium">
                    <span>{t('blog.readMore')}</span>
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-2 transition-transform" />
                  </div>
                </div>
              </motion.article>
            ))}
          </div>

          {/* Post Modal */}
          {selectedPost && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
              onClick={() => setSelectedPost(null)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 50 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 50 }}
                className="bg-background rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="sticky top-0 bg-background/80 backdrop-blur-lg border-b p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{selectedPost.date}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{selectedPost.readTime}</span>
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedPost(null)}
                    className="p-2 hover:bg-secondary rounded-full transition-colors"
                  >
                    ✕
                  </button>
                </div>
                <div className="p-8">
                  <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-primary/10 text-primary mb-4">
                    {selectedPost.category}
                  </span>
                  <h2 className="text-3xl font-bold mb-6">{selectedPost.title}</h2>
                  <div className="prose dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {selectedPost.content}
                    </ReactMarkdown>
                  </div>

                  {/* Comments Section */}
                  <div className="mt-12 pt-8 border-t">
                    <h3 className="text-xl font-semibold mb-4 flex items-center">
                      <MessageCircle className="w-5 h-5 mr-2" />
                      Comments
                    </h3>
                    <div className="bg-secondary/50 rounded-xl p-6 text-center">
                      <p className="text-muted-foreground mb-4">
                        Comments powered by Giscus (GitHub Discussions)
                      </p>
                      <p className="text-sm text-muted-foreground">
                        To set up comments, configure Giscus with your GitHub repository.
                        <br />
                        <a 
                          href="https://giscus.app" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          Learn more →
                        </a>
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
