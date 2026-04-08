import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, Lock, FileText } from 'lucide-react';
import Watermark from '../components/Watermark';

export default function NoteViewer() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  // 基础安全：禁止右键、禁止 F12
  useEffect(() => {
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
        e.preventDefault();
      }
    };

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // 构建 PDF 路径
  const pdfUrl = `/assets/pdf/${slug}.pdf#toolbar=0&navpanes=0&scrollbar=1`;

  // 返回主页
  const handleBack = () => {
    navigate('/');
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 overflow-hidden select-none">
      {/* 顶部安全状态栏 */}
      <nav className="h-14 border-b border-white/10 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button 
            onClick={handleBack}
            className="flex items-center text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 mr-1 group-hover:-translate-x-1 transition-transform" />
            返回列表
          </button>
          <div className="h-4 w-[1px] bg-white/10" />
          <div className="flex items-center text-slate-300 font-medium">
            <FileText className="w-4 h-4 mr-2 text-primary" />
            {slug} - 专供阅读
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center text-[10px] uppercase tracking-wider text-primary/80 bg-primary/10 px-3 py-1 rounded-full border border-primary/20">
            <Lock className="w-3 h-3 mr-1" />
            Encrypted Source
          </div>
          <div className="flex items-center text-[10px] uppercase tracking-wider text-amber-500/80 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
            <ShieldAlert className="w-3 h-3 mr-1" />
            Anti-Theft Active
          </div>
        </div>
      </nav>

      {/* 核心内容区 */}
      <div className="relative flex-1 bg-slate-800">
        {/* 全屏隐形水印层 */}
        <div className="absolute inset-0 z-[100] pointer-events-none opacity-[0.12]">
          <Watermark />
        </div>

        {/* Loading 状态 */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="mt-4 text-slate-400 text-sm">正在解密安全文档...</p>
            </div>
          </div>
        )}
        
        <iframe
          src={pdfUrl}
          className="w-full h-full border-none"
          onLoad={() => setLoading(false)}
          title="Security Document Viewer"
        />

        {/* 底部提示 */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[110] pointer-events-none px-6 py-2 bg-black/60 backdrop-blur-sm rounded-full border border-white/10">
          <p className="text-[10px] text-white/40 whitespace-nowrap">
            © WooToot 版权所有 · 本页面已开启全轨迹数字加密水印 · 违规传播将追究法律责任
          </p>
        </div>
      </div>
    </div>
  );
}
