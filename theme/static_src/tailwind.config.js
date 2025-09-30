/**
 * Configuración de Tailwind CSS v3 para SlideMotion
 */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../../templates/**/*.{html,js}',
    '../../**/templates/**/*.html',
    '../../**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2563eb',
        'secondary': '#64748b',
      },
      fontFamily: {
        'sans': ['Nunito', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}