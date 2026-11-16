/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#2563EB',      // Enterprise Blue (actions, links, focus)
          primaryHover: '#1D4ED8', // Darker Blue
          secondary: '#0F172A',    // Deep Slate (Sidebar, dark headers)
          sidebarHover: '#1E293B', // Slate-800
          success: '#16A34A',      // Success Green (Approved, Checked-In)
          warning: '#F59E0B',      // Warning Amber (Pending)
          danger: '#DC2626',       // Danger Red (Rejected, Overstay)
          neutral: '#64748B',      // Neutral Slate (Captions, inactive)
          canvas: '#F8FAFC',       // Slate-50 Background
          surface: '#FFFFFF',      // White cards & panels
          border: '#E2E8F0',       // Slate-200 Subtle Borders
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
};

