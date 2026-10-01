/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0f',
        primary: '#60a5fa', // soft blue
        secondary: '#a78bfa', // soft purple
        accent: '#34d399', // soft green
        danger: '#fb7185', // soft red
        warning: '#fbbf24', // soft yellow
        muted: '#9ca3af',
        glass: {
          10: 'rgba(255, 255, 255, 0.03)',
          20: 'rgba(255, 255, 255, 0.05)',
          30: 'rgba(255, 255, 255, 0.1)',
          border: 'rgba(255, 255, 255, 0.08)'
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'roll': 'roll 20s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        roll: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '-1000px 1000px' },
        }
      }
    },
  },
  plugins: [],
}
