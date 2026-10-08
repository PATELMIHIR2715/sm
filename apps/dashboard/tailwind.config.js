/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        tv: {
          bg: '#131722',
          surface: '#1e222d',
          elevated: '#2a2e39',
          hover: '#363a45',
          border: '#2a2e39',
          borderLight: '#363a45',
          blue: '#2962ff',
          blueHover: '#1e53e5',
          blueMuted: 'rgba(41, 98, 255, 0.15)',
          text: '#d1d4dc',
          textMuted: '#787b86',
          textBright: '#f0f3fa',
          green: '#089981',
          red: '#f23645',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
