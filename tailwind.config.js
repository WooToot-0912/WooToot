/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // 补全所有用到的自定义颜色（包括 muted-foreground）
      colors: {
        background: '#ffffff',
        foreground: '#111827',
        border: '#e5e7eb',
        secondary: '#f3f4f6',
        primary: '#3b82f6',
        'muted-foreground': '#6b7280', // 新增 muted-foreground 对应的颜色
        muted: '#f9fafb', // 建议补充，避免后续报错
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'gradient': 'gradient 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
    },
  },
  plugins: [],
}
