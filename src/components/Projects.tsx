import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, Github, ArrowRight, X } from 'lucide-react';

const projects = [
  {
    id: 1,
    title: 'E-Commerce Platform',
    description: 'A full-featured e-commerce platform with real-time inventory, payment processing, and admin dashboard.',
    image: 'E-Commerce',
    tags: ['React', 'Node.js', 'PostgreSQL', 'Stripe'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Built a scalable e-commerce solution handling 10k+ daily active users. Implemented real-time inventory management using WebSockets and integrated Stripe for payments.',
  },
  {
    id: 2,
    title: 'Task Management App',
    description: 'Collaborative task management tool with real-time updates, team workspaces, and advanced filtering.',
    image: 'Task App',
    tags: ['Next.js', 'TypeScript', 'Prisma', 'Socket.io'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Developed a Trello-like application with drag-and-drop functionality, real-time collaboration features, and comprehensive team management tools.',
  },
  {
    id: 3,
    title: 'AI Content Generator',
    description: 'AI-powered content generation tool that helps creators write blog posts, social media content, and more.',
    image: 'AI Tool',
    tags: ['Python', 'FastAPI', 'OpenAI', 'React'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Integrated OpenAI GPT-4 API to create an intelligent writing assistant. Features include tone adjustment, length control, and multi-language support.',
  },
  {
    id: 4,
    title: 'Portfolio Dashboard',
    description: 'Interactive dashboard for tracking investments, visualizing portfolio performance, and market analysis.',
    image: 'Dashboard',
    tags: ['Vue.js', 'D3.js', 'Firebase', 'Tailwind'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Created a comprehensive financial dashboard with real-time data visualization, interactive charts using D3.js, and personalized investment insights.',
  },
  {
    id: 5,
    title: 'Social Media Analytics',
    description: 'Analytics platform for social media managers to track engagement, growth, and content performance.',
    image: 'Analytics',
    tags: ['React', 'GraphQL', 'AWS', 'Chart.js'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Built a comprehensive analytics platform processing millions of data points. Features include automated reporting, competitor analysis, and trend prediction.',
  },
  {
    id: 6,
    title: 'Weather Application',
    description: 'Beautiful weather app with location-based forecasts, interactive maps, and severe weather alerts.',
    image: 'Weather',
    tags: ['React Native', 'Expo', 'Weather API', 'Maps'],
    demoUrl: 'https://example.com',
    repoUrl: 'https://github.com',
    details: 'Developed cross-platform mobile app with accurate weather forecasting, interactive radar maps, and push notifications for weather alerts.',
  },
];

export function Projects() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [selectedProject, setSelectedProject] = useState<typeof projects[0] | null>(null);

  return (
    <section id="projects" className="py-24 md:py-32">
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
              {t('projects.title')}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-lg max-w-2xl mx-auto"
            >
              {t('projects.subtitle')}
            </motion.p>
          </div>

          {/* Projects Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {projects.map((project, index) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ y: -10 }}
                className="group bg-card rounded-2xl overflow-hidden border border-border hover:border-primary/50 transition-all cursor-pointer"
                onClick={() => setSelectedProject(project)}
              >
                <div className="aspect-video bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold text-foreground/20">{project.image}</span>
                  </div>
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-4">
                    <motion.a
                      href={project.demoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-3 bg-white rounded-full text-black"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="w-5 h-5" />
                    </motion.a>
                    <motion.a
                      href={project.repoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-3 bg-white rounded-full text-black"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Github className="w-5 h-5" />
                    </motion.a>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
                    {project.title}
                  </h3>
                  <p className="text-muted-foreground mb-4 line-clamp-2">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {project.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 text-xs rounded-md bg-secondary text-secondary-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center text-primary font-medium text-sm">
                    <span>View Details</span>
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-2 transition-transform" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Project Modal */}
          {selectedProject && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
              onClick={() => setSelectedProject(null)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 50 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 50 }}
                className="bg-background rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="relative aspect-video bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-5xl font-bold text-foreground/20">{selectedProject.image}</span>
                  </div>
                  <button
                    onClick={() => setSelectedProject(null)}
                    className="absolute top-4 right-4 p-2 bg-black/20 hover:bg-black/40 rounded-full transition-colors"
                  >
                    <X className="w-5 h-5 text-white" />
                  </button>
                </div>
                <div className="p-8">
                  <h2 className="text-3xl font-bold mb-4">{selectedProject.title}</h2>
                  <p className="text-muted-foreground mb-6">{selectedProject.details}</p>

                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-muted-foreground mb-2">{t('projects.technologies')}</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedProject.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex space-x-4">
                    <motion.a
                      href={selectedProject.demoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-medium"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span>{t('projects.viewProject')}</span>
                    </motion.a>
                    <motion.a
                      href={selectedProject.repoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 border-2 border-border hover:border-foreground/40 rounded-full font-medium"
                    >
                      <Github className="w-4 h-4" />
                      <span>{t('projects.viewCode')}</span>
                    </motion.a>
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
