import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Calendar, Clock, ArrowRight, MessageCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function Blog() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const postKeys = ['post1', 'post2', 'post3'];
  const blogPosts = postKeys.map((key, index) => ({
    id: index + 1,
    title: t(`blog.posts.${key}.title`),
    excerpt: t(`blog.posts.${key}.excerpt`),
    category: t(`blog.posts.${key}.category`),
    date: ['2024-03-15', '2024-03-10', '2024-03-05'][index],
    readTime: ['8 min read', '6 min read', '10 min read'][index],
    slug: key,
    content: `Detailed content for ${key} would go here...`
  }));

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
