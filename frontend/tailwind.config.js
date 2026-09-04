/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: '#FFFFFF',
          secondaryBg: '#F7FAFF',
          text: '#0F172A',
          subtext: '#64748B',
          border: '#E2E8F0',
          blue: {
            DEFAULT: '#2563EB',
            light: '#60A5FA',
            soft: '#EFF6FF',
            hover: '#1D4ED8',
          },
          purple: '#7C3AED',
          green: '#16A34A',
          amber: '#F59E0B',
          red: '#EF4444',
        }
      }
    },
  },
  plugins: [],
}


