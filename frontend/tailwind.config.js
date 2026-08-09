/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#ffffff',
          900: '#f8fafc',
          850: '#f1f5f9',
          800: '#ffffff',
          750: '#e2e8f0',
          700: '#cbd5e1',
        },
        brand: {
          600: '#0369a1',
          500: '#0284c7',
          400: '#0ea5e9',
          300: '#38bdf8',
          200: '#7dd3fc',
          cyan: '#06b6d4',
          amber: '#d97706',
          gold: '#f59e0b',
          sky: '#0284c7',
          azure: '#0284c7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%)',
        'brand-gradient': 'linear-gradient(135deg, #0369a1 0%, #0284c7 50%, #38bdf8 100%)',
        'gold-gradient': 'linear-gradient(135deg, #d97706 0%, #f59e0b 50%, #fbbf24 100%)',
        'sky-glow': 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(14, 165, 233, 0.18), transparent 70%)',
        'animated-sky-mesh': 'linear-gradient(-45deg, #f8fafc, #f1f5f9, #e0f2fe, #f0f9ff, #f8fafc)',
        'animated-text-gradient': 'linear-gradient(135deg, #0f172a 0%, #0284c7 35%, #0ea5e9 70%, #d97706 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'gradient-flow': 'gradientFlow 12s ease infinite',
        'gradient-shift': 'gradientShift 5s ease infinite',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(14, 165, 233, 0.25)' },
          '100%': { boxShadow: '0 0 30px rgba(14, 165, 233, 0.6)' },
        },
        gradientFlow: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        gradientShift: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        pulseGlow: {
          '0%': { opacity: '0.4', transform: 'scale(1)' },
          '100%': { opacity: '0.8', transform: 'scale(1.05)' },
        }
      }
    },
  },
  plugins: [],
}

