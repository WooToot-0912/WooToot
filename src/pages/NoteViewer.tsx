import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, ShieldAlert, Lock } from 'lucide-react';
import Watermark from '../components/Watermark';

export default function NoteViewer({ slug, onClose }: { slug: string; onClose: () => void }) {
  const [content, setContent] = useState('');

  // 模拟加载本地 markdown 内容
  // 实际生产中可以配合 Vite 的 glob import
  useEffect(() => {
    // 这里硬编码加载我们刚刚拷贝的内容字符串（为了演示和稳定）
    // 之后可以通过 fetch 或 dynamic import 扩展建议
    const loadContent = async () => {
      try {
          // 这里我们简单处理，直接把读取到的内容作为演示
          // 实际操作中，我们会将内容导出为一个常量或通过 fetch 加载
          const res = await fetch(`/src/content/blog/${slug}.md`);
          if (res.ok) {
              const text = await res.text();
              setContent(text);
          } else {
              setContent('# 笔记内容加载失败，请检查文件是否存在。\n\n我们将很快更新更多内容。');
          }
      } catch (e) {
          console.error(e);
      }
    };
    loadContent();

    // --- 安全保护逻辑 ---
    
    // 1. 禁止右键
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    // 2. 禁止选中（JS 兜底）
    const handleSelectStart = (e: Event) => e.preventDefault();
    // 3. 禁止复制和快捷键
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        (e.ctrlKey && (e.key === 'c' || e.key === 'u' || e.key === 'p' || e.key === 's')) || 
        e.key === 'F12'
      ) {
        e.preventDefault();
        alert('此内容受版权保护 (WooToot)，禁止复制或打印。');
        return false;
      }
    };

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('selectstart', handleSelectStart);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('selectstart', handleSelectStart);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [slug]);

  return (
    <div className="min-h-screen bg-background text-foreground relative selection:bg-transparent">
      {/* 隐形平铺水印 */}
      <Watermark text="WooToot" opacity={0.04} fontSize={22} gap={180} />
      
      {/* 顶部导航 */}
      <nav className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <button 
            onClick={onClose}
            className="flex items-center text-muted-foreground hover:text-primary transition-colors"
          >
            <ArrowLeft className="w-5 h-5 mr-1" />
            返回主页
          </button>
          <div className="flex items-center text-xs font-medium text-primary/60 bg-primary/5 px-3 py-1 rounded-full border border-primary/10">
            <Lock className="w-3 h-3 mr-1" />
            版权保护模式 (Anti-Copy)
          </div>
        </div>
      </nav>

      {/* 主体内容 */}
      <main className="max-w-4xl mx-auto px-4 py-12 md:py-20 relative">
        <div className="mb-10 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <p className="text-sm">
             <strong>版权提示：</strong> 本笔记受专利与版权保护。系统已开启全屏隐形水印（WooToot）和行为监控，任何截屏、录屏或尝试解析源码的行为均会带有版权标记。
          </p>
        </div>

        <article className="prose prose-lg dark:prose-invert max-w-none 
          [user-select:none] 
          [&_img]:pointer-events-none 
          [&_pre]:bg-secondary/50 [&_pre]:rounded-xl [&_pre]:p-6
          [&_h1]:text-4xl [&_h1]:font-bold [&_h1]:mb-8
          [&_h2]:text-2xl [&_h2]:mt-12 [&_h2]:mb-6 [&_h2]:border-b [&_h2]:pb-2
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </article>

        {/* 底部版权声明 */}
        <footer className="mt-24 pt-8 border-t text-center text-muted-foreground text-sm">
          <p>© {new Date().getFullYear()} WooToot. All rights reserved.</p>
          <p className="mt-2">未经许可，严禁转载或作为商业用途使用。</p>
        </footer>
      </main>

      {/* 打印时显示的深色水印逻辑 (CSS) */}
      <style>{`
        @media print {
          body { display: none; }
        }
        ::selection {
          background: transparent;
        }
      `}</style>
    </div>
  );
}
