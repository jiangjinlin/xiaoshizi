/** @type {import('tailwindcss').Config} */
// Tailwind v4 使用 ESM 配置导出格式；原先的 module.exports 是 v3 风格，
// 会触发 “looks like it might be for a different Tailwind CSS version” 警告。
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#4f46e5'
      },
      borderRadius: {
        'none': '0px',
        'sm': '2px',
        DEFAULT: '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
        'full': '9999px',
        'button': '4px'
      }
    },
  },
  plugins: [],
};
