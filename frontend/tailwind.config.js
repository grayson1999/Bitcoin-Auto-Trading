/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#FEFCE8',
          100: '#FEF9C3',
          400: '#FACC15', // Banana Yellow (vibrant)
          500: '#EAB308',
          600: '#CA8A04', // Nano Gold
          700: '#A16207',
        },
        // Re-aliasing for backward compatibility if needed, or just switch usage
        banana: {
          400: '#FACC15', // Primary Accent
          500: '#EAB308',
        },
        dark: {
          bg: '#0B0E14',      // Deepest Black/Blue
          surface: '#151921', // Lighter Surface
          border: 'rgba(255, 255, 255, 0.08)', // Subtle border
          text: {
            primary: '#F1F5F9',   // Slate 100
            secondary: '#94A3B8', // Slate 400
            muted: '#64748B',     // Slate 500
          }
        },
        accent: {
          purple: '#8b5cf6', // Violet
          pink: '#ec4899',   // Pink
          cyan: '#06b6d4',   // Cyan
          emerald: '#10b981', // Emerald
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass': 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)',
        'nano-pattern': "url('/nano-bg.png')", // We will generate this
      }
    },
  },
  plugins: [],
};
