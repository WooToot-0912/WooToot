import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BookOpen, Calendar, ArrowRight, Clock } from 'lucide-react';

export function LearningNotes() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  // 模拟动态数据（与 Blog.tsx 类似的逻辑）
  const uploadDate = new Date().toISOString().split('T')[0];
  const lastVisitorTime = () => {
    const mins = Math.floor(Math.random() * 55) + 5;
    return `${mins} min ago`;
  };

  const noteKeys = ['note1', 'note2', 'note3', 'note4', 'note5', 'note6', 'note7', 'note8'];
  
  // PDF 文件名映射
  const pdfMapping: Record<string, string> = {
    note1: '01_嵌入式项目概述和环境搭建',
    note2: '02_Linux系统开发',
    note3: '03_openHarmony开发',
    note4: 'BS和CS',
    note5: 'C#学习',
    note6: 'Csharp上位机实战：多线程编程（线程同步，事件触发，资源共享）',
    note7: 'OPC UA客户端与服务端通信',
    note8: 'python实训'
  };

  const learningNotes = noteKeys.map((key, index) => ({
    id: index + 1,
    title: t(`notes.items.${key}.title`),
    summary: t(`notes.items.${key}.summary`),
    category: t(`notes.items.${key}.category`),
    date: uploadDate,
    lastActive: lastVisitorTime(),
    slug: pdfMapping[key]
  }));

  return (
    <section id="notes" className="py-24 md:py-32 bg-background">
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
              {t('notes.title')}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-lg max-w-2xl mx-auto"
            >
              {t('notes.subtitle')}
            </motion.p>
          </div>

          {/* Notes Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {learningNotes.map((note, index) => (
              <motion.article
                key={note.id}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.2 + index * 0.05 }}
                whileHover={{ y: -5 }}
                className="group glass-card rounded-xl p-6 hover:border-primary/50 cursor-pointer relative flex flex-col h-full"
                onClick={() => navigate(`/note/${note.slug}`)}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-medium px-2 py-1 rounded bg-secondary text-secondary-foreground uppercase tracking-widest">
                    {note.category}
                  </span>
                </div>

                <h3 className="text-lg font-bold mb-3 group-hover:text-primary transition-colors line-clamp-2 leading-tight">
                  {note.title}
                </h3>
                
                <p className="text-muted-foreground text-sm mb-6 line-clamp-3 italic">
                  "{note.summary}"
                </p>

                <div className="mt-auto pt-4 border-t border-border/50 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {note.date}
                    </span>
                    <span className="flex items-center gap-1 text-primary/70">
                      <Clock className="w-3 h-3" />
                      {note.lastActive}
                    </span>
                  </div>
                  
                  <div className="flex items-center text-primary text-sm font-semibold mt-2 group-hover:translate-x-1 transition-transform">
                    {t('notes.viewNote')}
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </div>
                </div>
              </motion.article>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
