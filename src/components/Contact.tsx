import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, Send, Github, Twitter, Linkedin, CheckCircle, AlertCircle } from 'lucide-react';

export function Contact() {
  const { t } = useTranslation();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [showWechat, setShowWechat] = useState(false);
  const [formState, setFormState] = useState({
    name: '',
    email: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    // In production, replace this with actual form handling service like Formspree
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setIsSubmitting(false);
    setSubmitStatus('success');
    setFormState({ name: '', email: '', message: '' });

    setTimeout(() => setSubmitStatus('idle'), 5000);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormState((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const contactInfo = [
    { icon: Mail, label: t('contact.email'), value: '1950383511@qq.com', href: 'mailto:1950383511@qq.com' },
    { 
      icon: () => (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-primary">
          <path d="M8.225 3.197c-3.953 0-7.158 2.656-7.158 5.928 0 1.83.992 3.473 2.54 4.606l-.64 2.316 2.138-1.118c.365.097.74.153 1.12.153.284 0 .563-.03.834-.077-.253-.55-.39-1.16-.39-1.808 0-2.457 2.05-4.453 4.544-4.505-.515-3.13-4.04-5.495-3-5.495zm-3.023 3.52c-.443 0-.802-.348-.802-.78s.359-.78.802-.78.802.348.802.78-.359.78-.802.78zm3.626 0c-.443 0-.802-.348-.802-.78s.359-.78.802-.78.802.348.802.78-.359.78-.802.78zm10.744 3.916c-3.294 0-5.965 2.213-5.965 4.94 0 1.523.826 2.894 2.116 3.838l-.534 1.93 1.782-.931c.3.08.618.128.948.128.324 0 .638-.046.94-.132.8-.822 1.29-1.927 1.29-3.14 0-2.42-1.74-4.43-4.08-4.633a5.21 5.21 0 0 1 .494-.02zM14.63 13.1c-.368 0-.668-.29-.668-.65s.3-.65.668-.65.668.29.668.65-.3.65-.668.65zm3.023 0c-.368 0-.668-.29-.668-.65s.3-.65.668-.65.668.29.668.65-.3.65-.668.65z"/>
        </svg>
      ), 
      label: t('contact.wechat'), 
      value: 'Scan QR Code', 
      isWechat: true 
    },
    { icon: MapPin, label: t('contact.location'), value: 'Remote / Worldwide', href: '#' },
  ];

  const socialLinks = [
    { icon: Github, label: 'GitHub', href: 'https://github.com' },
    { icon: Twitter, label: 'Twitter', href: 'https://twitter.com' },
    { icon: Linkedin, label: 'LinkedIn', href: 'https://linkedin.com' },
  ];

  return (
    <section id="contact" className="py-24 md:py-32 bg-secondary/30">
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
              {t('contact.title')}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-lg max-w-2xl mx-auto"
            >
              {t('contact.subtitle')}
            </motion.p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Info */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.4 }}
              className="space-y-8"
            >
              <div className="space-y-6">
                {contactInfo.map((item, index) => (
                  <motion.div
                    key={item.label}
                    onClick={() => item.isWechat ? setShowWechat(!showWechat) : item.href && window.open(item.href, '_blank')}
                    initial={{ opacity: 0, y: 20 }}
                    animate={isInView ? { opacity: 1, y: 0 } : {}}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    whileHover={{ x: 5 }}
                    className="flex items-center space-x-4 p-4 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors cursor-pointer"
                  >
                    <div className="p-3 rounded-lg bg-primary/10">
                      {index === 1 ? (
                        <item.icon />
                      ) : (
                        item.icon && <item.icon className="w-6 h-6 text-primary" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{item.label}</p>
                      <p className="font-medium font-inter">{item.value}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* WeChat QR Hover/Popup */}
              {showWechat && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  className="p-6 bg-card border border-border rounded-2xl shadow-xl flex flex-col items-center space-y-4 max-w-[280px] mx-auto lg:mx-0"
                >
                  <div className="relative group">
                    <img 
                      src="/images/wechat-qr.png" 
                      alt="WeChat QR Code" 
                      className="w-48 h-48 rounded-lg shadow-inner"
                    />
                    <div className="absolute inset-0 bg-primary/5 rounded-lg pointer-events-none" />
                  </div>
                  <p className="text-sm text-muted-foreground text-center font-medium">
                    {t('contact.scanWechat')}
                  </p>
                </motion.div>
              )}

              <div>
                <h3 className="text-lg font-semibold mb-4">Follow Me</h3>
                <div className="flex space-x-4">
                  {socialLinks.map((social, index) => (
                    <motion.a
                      key={social.label}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      initial={{ opacity: 0, scale: 0 }}
                      animate={isInView ? { opacity: 1, scale: 1 } : {}}
                      transition={{ delay: 0.7 + index * 0.1 }}
                      whileHover={{ scale: 1.2, y: -5 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-4 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors"
                      aria-label={social.label}
                    >
                      <social.icon className="w-6 h-6" />
                    </motion.a>
                  ))}
                </div>
              </div>

              <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 border border-border">
                <h3 className="font-semibold mb-2">Open for Opportunities</h3>
                <p className="text-sm text-muted-foreground">
                  I'm currently available for freelance projects and full-time positions. 
                  Let's build something amazing together!
                </p>
              </div>
            </motion.div>

            {/* Contact Form */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.5 }}
            >
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium mb-2">
                    {t('contact.name')}
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formState.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-card border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                    placeholder="John Doe"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium mb-2">
                    {t('contact.email')}
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formState.email}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-card border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                    placeholder="john@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium mb-2">
                    {t('contact.message')}
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formState.message}
                    onChange={handleChange}
                    required
                    rows={5}
                    className="w-full px-4 py-3 rounded-xl bg-card border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none"
                    placeholder="Tell me about your project..."
                  />
                </div>

                <motion.button
                  type="submit"
                  disabled={isSubmitting}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full flex items-center justify-center space-x-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>{t('contact.sending')}</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      <span>{t('contact.send')}</span>
                    </>
                  )}
                </motion.button>

                {/* Status Messages */}
                {submitStatus === 'success' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center space-x-2 p-4 rounded-xl bg-green-500/10 text-green-600"
                  >
                    <CheckCircle className="w-5 h-5" />
                    <span>{t('contact.success')}</span>
                  </motion.div>
                )}

                {submitStatus === 'error' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center space-x-2 p-4 rounded-xl bg-red-500/10 text-red-600"
                  >
                    <AlertCircle className="w-5 h-5" />
                    <span>{t('contact.error')}</span>
                  </motion.div>
                )}
              </form>

              <p className="mt-4 text-sm text-muted-foreground text-center">
                Form powered by Formspree. 
                <a 
                  href="https://formspree.io" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline ml-1"
                >
                  Learn more
                </a>
              </p>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
