import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Code2, Palette, Terminal, Database, Globe, Cpu } from 'lucide-react';

const skills = [
  { icon: Code2, name: 'Frontend', items: ['React', 'Vue', 'TypeScript', 'Tailwind CSS'] },
  { icon: Terminal, name: 'Backend', items: ['Node.js', 'Python', 'Go', 'PostgreSQL'] },
  { icon: Database, name: 'Database', items: ['PostgreSQL', 'MongoDB', 'Redis', 'Prisma'] },
  { icon: Globe, name: 'DevOps', items: ['Docker', 'Kubernetes', 'CI/CD', 'AWS'] },
  { icon: Palette, name: 'Design', items: ['Figma', 'Adobe XD', 'UI/UX', 'Motion'] },
  { icon: Cpu, name: 'Tools', items: ['Git', 'VS Code', 'Vim', 'Linux'] },
];

const experiences = [
  {
    period: '2022 - Present',
    title: 'Senior Full Stack Developer',
    company: 'Tech Company',
    description: 'Leading development of scalable web applications and mentoring junior developers.',
  },
  {
    period: '2020 - 2022',
    title: 'Full Stack Developer',
    company: 'Startup',
    description: 'Built and deployed multiple web applications from scratch using modern technologies.',
  },
  {
    period: '2018 - 2020',
    title: 'Frontend Developer',
    company: 'Digital Agency',
    description: 'Developed responsive websites and web applications for various clients.',
  },
];

export function About() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="about" className="py-24 md:py-32 relative">
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
              {t('about.title')}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-lg max-w-2xl mx-auto"
            >
              {t('about.subtitle')}
            </motion.p>
          </div>

          {/* About Content */}
          <div className="grid lg:grid-cols-2 gap-12 items-center mb-20">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.4 }}
              className="space-y-6"
            >
              <p className="text-lg text-muted-foreground leading-relaxed">
                {t('about.description')}
              </p>
              <p className="text-lg text-muted-foreground leading-relaxed">
                When I'm not coding, you can find me exploring new technologies, contributing to open source projects, 
                or sharing my knowledge through blog posts and tutorials.
              </p>
              <div className="flex items-center space-x-4 pt-4">
                <div className="text-center">
                  <div className="text-3xl font-bold gradient-text">5+</div>
                  <div className="text-sm text-muted-foreground">Years Experience</div>
                </div>
                <div className="w-px h-12 bg-border" />
                <div className="text-center">
                  <div className="text-3xl font-bold gradient-text">50+</div>
                  <div className="text-sm text-muted-foreground">Projects Completed</div>
                </div>
                <div className="w-px h-12 bg-border" />
                <div className="text-center">
                  <div className="text-3xl font-bold gradient-text">20+</div>
                  <div className="text-sm text-muted-foreground">Happy Clients</div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.5 }}
              className="relative"
            >
              <div className="aspect-square rounded-2xl overflow-hidden bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 p-1">
                <div className="w-full h-full rounded-xl bg-secondary flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-32 h-32 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-4xl font-bold">
                      682049
                    </div>
                    <p className="text-muted-foreground">Your Photo Here</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Skills */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.6 }}
            className="mb-20"
          >
            <h3 className="text-2xl font-bold mb-8 text-center">{t('about.skills')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {skills.map((skill, index) => (
                <motion.div
                  key={skill.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  whileHover={{ y: -5, scale: 1.02 }}
                  className="p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors group"
                >
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                      <skill.icon className="w-6 h-6 text-primary" />
                    </div>
                    <h4 className="font-semibold">{skill.name}</h4>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {skill.items.map((item) => (
                      <span
                        key={item}
                        className="px-3 py-1 text-sm rounded-full bg-secondary text-secondary-foreground"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Experience */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.8 }}
          >
            <h3 className="text-2xl font-bold mb-8 text-center">{t('about.experience')}</h3>
            <div className="space-y-6">
              {experiences.map((exp, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ delay: 0.9 + index * 0.1 }}
                  className="relative pl-8 md:pl-0"
                >
                  <div className="md:grid md:grid-cols-[200px_1fr] md:gap-8">
                    <div className="text-sm text-muted-foreground font-medium mb-2 md:mb-0 md:text-right">
                      {exp.period}
                    </div>
                    <div className="relative pb-8 border-l border-border md:border-l-0 md:pb-0">
                      <div className="absolute -left-[33px] top-0 w-4 h-4 rounded-full bg-primary md:hidden" />
                      <h4 className="font-semibold text-lg">{exp.title}</h4>
                      <p className="text-primary font-medium mb-2">{exp.company}</p>
                      <p className="text-muted-foreground">{exp.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
