import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, Lock, FileText, Download, Loader2 } from 'lucide-react';
import Watermark from '../components/Watermark';
import { PDFDocument, rgb, StandardFonts, degrees } from 'pdf-lib';

export default function NoteViewer() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [isBlurred, setIsBlurred] = useState(false);

  // 严苛防御：拦截所有可能窃取内容的快捷键
  useEffect(() => {
    const preventDefault = (e: Event) => e.preventDefault();
    
    const handleKeyDown = (e: KeyboardEvent) => {
      // 禁止 F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U (源码)
      if (
        e.key === 'F12' || 
        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) ||
        (e.ctrlKey && e.key === 'u')
      ) {
        e.preventDefault();
        return false;
      }

      // 禁止 复制(Ctrl+C), 剪切(Ctrl+X), 全选(Ctrl+A), 打印(Ctrl+P), 保存(Ctrl+S)
      if (e.ctrlKey && ['c', 'x', 'a', 'p', 's'].includes(e.key.toLowerCase())) {
        e.preventDefault();
        return false;
      }

      // 拦截某些截屏工具常用快捷键 (如 Alt+A, Win+Shift+S 等尽量拦截)
      if ((e.altKey && e.key.toLowerCase() === 'a') || (e.metaKey && e.shiftKey && e.key.toLowerCase() === 's')) {
        setIsBlurred(true); // 瞬间模糊
        setTimeout(() => setIsBlurred(false), 2000);
      }
    };

    // 监听窗口失焦/可见性变化：防止隐藏截图或切换录屏
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setIsBlurred(true);
      } else {
        setIsBlurred(false);
      }
    };

    const handleBlur = () => setIsBlurred(true);
    const handleFocus = () => setIsBlurred(false);

    window.addEventListener('blur', handleBlur);
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('contextmenu', preventDefault);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('copy', preventDefault);
    document.addEventListener('cut', preventDefault);
    document.addEventListener('selectstart', preventDefault);

    return () => {
      window.removeEventListener('blur', handleBlur);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('contextmenu', preventDefault);
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('copy', preventDefault);
      document.removeEventListener('cut', preventDefault);
      document.removeEventListener('selectstart', preventDefault);
    };
  }, []);

  // 带实时水印的 PDF 处理与下载
  const handleSafeDownload = async () => {
    try {
      setExporting(true);
      const originalPdfUrl = `/assets/pdf/${slug}.pdf`;
      const response = await fetch(originalPdfUrl);
      const existingPdfBytes = await response.arrayBuffer();

      // 加载 PDF 字节
      const pdfDoc = await PDFDocument.load(existingPdfBytes);
      const helveticaFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
      const pages = pdfDoc.getPages();
      
      const watermarkText = `WooToot Secure Source - ${new Date().toLocaleString()}`;

      // 遍历所有页面并注入水印
      pages.forEach((page) => {
        const { width, height } = page.getSize();
        
        // 绘制多次以覆盖全屏
        for (let x = 50; x < width; x += 250) {
          for (let y = 50; y < height; y += 200) {
            page.drawText(watermarkText, {
              x: x,
              y: y,
              size: 12,
              font: helveticaFont,
              color: rgb(0.7, 0.7, 0.7),
              rotate: degrees(45),
              opacity: 0.15,
            });
          }
        }
      });

      const pdfBytes = await pdfDoc.save();
      const blob = new Blob([pdfBytes as any], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `[Protected] ${slug}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Safe download failed:', error);
      alert('安全提取失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  const pdfUrl = `/assets/pdf/${slug}.pdf#toolbar=0&navpanes=0&scrollbar=1`;

  return (
    <div className={`flex flex-col h-screen bg-slate-900 transition-all duration-500 overflow-hidden select-none ${isBlurred ? 'blur-3xl grayscale' : ''}`}>
      <nav className="h-14 border-b border-white/10 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 z-50">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 mr-1 group-hover:-translate-x-1 transition-transform" />
            返回列表
          </button>
          <div className="h-4 w-[1px] bg-white/10" />
          <div className="flex items-center text-slate-300 font-medium">
            <FileText className="w-4 h-4 mr-2 text-primary" />
            {slug}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSafeDownload}
            disabled={exporting || loading}
            className="flex items-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 px-4 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
          >
            {exporting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            安全提取 (带溯源水印)
          </button>
          <div className="hidden md:flex items-center text-[10px] tracking-wider text-amber-500/80 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
            <ShieldAlert className="w-3 h-3 mr-1" />
            防盗保护中
          </div>
        </div>
      </nav>

      <div className="relative flex-1 bg-slate-800">
        {/* 全屏动态溯源水印 */}
        <Watermark text="WooToot" />

        {/* 安全遮盖层：当检测到可能截图时显示 */}
        {isBlurred && (
          <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-black/40 backdrop-blur-xl">
            <div className="text-center p-8 border border-white/10 rounded-2xl bg-slate-900/80">
              <Lock className="w-12 h-12 text-primary mx-auto mb-4 animate-pulse" />
              <h3 className="text-xl font-bold text-white mb-2">安全保护已激活</h3>
              <p className="text-slate-400 text-sm">由于检测到窗口失焦或潜在截图行为，内容已自动锁定。</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="mt-4 text-slate-400 text-sm">正在解密文档并加载动态水印...</p>
            </div>
          </div>
        )}
        
        <iframe
          src={pdfUrl}
          className="w-full h-full border-none"
          onLoad={() => setLoading(false)}
          title="Security Document Viewer"
        />

        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[110] pointer-events-none px-6 py-2 bg-black/60 backdrop-blur-sm rounded-full border border-white/10">
          <p className="text-[10px] text-white/60 whitespace-nowrap">
            © WooToot | 实时溯源 ID: {Math.random().toString(36).substring(7).toUpperCase()} | 违规录播必究
          </p>
        </div>
      </div>

      {/* 打印拦截样式 */}
      <style >{`
        @media print {
          body { display: none !important; }
        }
      `}</style>
    </div>
  );
}
