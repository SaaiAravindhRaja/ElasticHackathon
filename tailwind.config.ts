import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#1f6fff',
          red: '#e45757',
          green: '#23c16b'
        }
      }
    }
  },
  plugins: []
}

export default config
