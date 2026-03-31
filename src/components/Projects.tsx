import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, Github, ArrowRight, X } from 'lucide-react';

export function Projects() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const projects = [
    {
      id: 'p1',
      title: t('projects.list.p1.title'),
      description: t('projects.list.p1.description'),
      details: t('projects.list.p1.details'),
      image: '/images/projects/p1-tobacco.png',
      tags: ['YOLOv8', 'ECA Attention', 'Python', 'OpenCV'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E7%83%A4%E7%83%9F%E7%97%85%E5%AE%B3%E6%A3%80%E6%B5%8B%E9%A1%B9%E7%9B%AE',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E7%83%A4%E7%83%9F%E7%97%85%E5%AE%B3%E6%A3%80%E6%B5%8B%E9%A1%B9%E7%9B%AE',
    },
    {
      id: 'p2',
      title: t('projects.list.p2.title'),
      description: t('projects.list.p2.description'),
      details: t('projects.list.p2.details'),
      image: '/images/projects/p2-quant.png',
      tags: ['Python', 'OpenCV', 'Linear Regression', 'Threading'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E6%99%BA%E8%83%BD%E9%87%8F%E5%8C%96%E4%BA%A4%E6%98%93%E7%9B%91%E6%8E%A7%E7%B3%BB%E7%BB%9F',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E6%99%BA%E8%83%BD%E9%87%8F%E5%8C%96%E4%BA%A4%E6%98%93%E7%9B%91%E6%8E%A7%E7%B3%BB%E7%BB%9F',
    },
    {
      id: 'p3',
      title: t('projects.list.p3.title'),
      description: t('projects.list.p3.description'),
      details: t('projects.list.p3.details'),
      image: '/images/projects/p3-rpa.png',
      tags: ['Python', 'PyQt5', 'UI Automation', 'RPA'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E8%87%AA%E5%8A%A8%E4%BA%A4%E6%98%93%E6%9C%BA%E5%99%A8%E4%BA%BA-RPA',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/%E8%87%AA%E5%8A%A8%E4%BA%A4%E6%98%93%E6%9C%BA%E5%99%A8%E4%BA%BA-RPA',
    },
    {
      id: 'p4',
      title: t('projects.list.p4.title'),
      description: t('projects.list.p4.description'),
      details: t('projects.list.p4.details'),
      image: '/images/projects/p4-tsa.png',
      tags: ['Java', 'Servlet', 'JDBC', 'MySQL'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/TSA%E4%BC%81%E4%B8%9A%E7%BA%A7%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-JavaWeb',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/TSA%E4%BC%81%E4%B8%9A%E7%BA%A7%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-JavaWeb',
    },
    {
      id: 'p5',
      title: t('projects.list.p5.title'),
      description: t('projects.list.p5.description'),
      details: t('projects.list.p5.details'),
      image: '/images/projects/p5-ai.png',
      tags: ['Flask', 'OpenAI', 'WechatSI', 'JavaScript'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/AI%E6%99%BA%E8%83%BD%E8%AF%AD%E9%9F%B3%E5%8A%A9%E6%89%8B',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/AI%E6%99%BA%E8%83%BD%E8%AF%AD%E9%9F%B3%E5%8A%A9%E6%89%8B',
    },
    {
      id: 'p6',
      title: t('projects.list.p6.title'),
      description: t('projects.list.p6.description'),
      details: t('projects.list.p6.details'),
      image: '/images/projects/p6-qq.png',
      tags: ['C#', 'WinForms', 'MDI', 'SQL Server'],
      demoUrl: 'https://github.com/WooToot-0912/WooToot/tree/QQ%E7%99%BB%E5%BD%95%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-WinForm',
      repoUrl: 'https://github.com/WooToot-0912/WooToot/tree/QQ%E7%99%BB%E5%BD%95%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-WinForm',
    },
  ];

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
                  <img 
                    src={project.image} 
                    alt={project.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
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
                    <span>{t('projects.details')}</span>
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
                  <img 
                    src={selectedProject.image} 
                    alt={selectedProject.title}
                    className="w-full h-full object-cover"
                  />
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
