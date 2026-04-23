# EduMaht LMS AI - Frontend

React + Vite + Material-UI frontend untuk EduMaht Learning Management System dengan fitur AI.

## 🎨 Fitur UI

- **Modern Material Design** dengan Material-UI 5
- **Dark Mode & Light Mode** toggle
- **Responsive Design** untuk mobile, tablet, dan desktop
- **Authentication Pages**: Login & Register
- **Dashboard** dengan statistics dan course management
- **Shopping Cart** Material-UI icons
- **Real-time Updates** dengan Zustand state management
- **API Integration** dengan axios

## 🚀 Teknologi

- **React 18** - UI library
- **Vite** - Build tool
- **Material-UI 5** - UI component library
- **React Router 6** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React Hook Form** - Form management

## 📦 Instalasi

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` dengan konfigurasi Anda:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

### 3. Start Development Server

```bash
npm run dev
```

Frontend akan tersedia di: `http://localhost:3000`

## 📂 Struktur Project

```
frontend/
├── src/
│   ├── pages/              # Page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   └── ...
│   ├── components/         # Reusable components
│   │   ├── Layout.jsx      # Main layout with nav
│   │   └── ...
│   ├── services/           # API services
│   │   ├── api.js          # Axios instance
│   │   ├── authService.js
│   │   └── courseService.js
│   ├── stores/             # Zustand stores
│   │   └── authStore.js
│   ├── themes/             # Material-UI themes
│   │   └── theme.js        # Light & Dark themes
│   ├── hooks/              # Custom hooks
│   ├── utils/              # Utility functions
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html              # HTML template
├── vite.config.jsx         # Vite config
├── package.json
└── README.md
```

## 🎯 Pages & Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/login` | Login | User login page |
| `/register` | Register | User registration page |
| `/dashboard` | Dashboard | Main dashboard with courses |
| `/courses` | Courses | View all courses |
| `/course/:id` | CourseDetail | Course detail page |
| `/profile` | Profile | User profile page |
| `/settings` | Settings | User settings |

## 🔐 Authentication

### Login dengan Email/Password
```jsx
const { login } = useAuthStore()
await login(email, password)
```

### Login dengan Google
```jsx
const { googleLogin } = useAuthStore()
await googleLogin(tokenId)
```

### Logout
```jsx
const { logout } = useAuthStore()
logout()
```

## 🎨 Customization

### Mengubah Colors

Edit `src/themes/theme.js`:

```javascript
primary: {
  main: '#your-color',
  light: '#lighter-color',
  dark: '#darker-color',
},
```

### Menambah Dark Mode Colors

Customize di `darkTheme` di file yang sama.

### Custom Components

Material-UI components dapat di-override di `components` section theme:

```javascript
components: {
  MuiButton: {
    styleOverrides: {
      root: {
        // custom styles
      }
    }
  }
}
```

## 📡 API Integration

Semua API calls melalui `services/`:

```jsx
import { courseService } from './services/courseService'

// Get courses
const courses = await courseService.getCourses()

// Enroll in course
await courseService.enrollCourse(courseId)

// Get my courses
const myCourses = await courseService.getMyCourses()
```

## 🔄 State Management

Menggunakan Zustand untuk state management:

```jsx
import { useAuthStore } from './stores/authStore'

export default function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuthStore()
  
  return (...)
}
```

## 🚀 Build & Deployment

### Build untuk Production

```bash
npm run build
```

Output akan di folder `dist/`.

### Preview Production Build

```bash
npm run preview
```

## 🧪 Linting

```bash
npm run lint
```

## 📝 Development Guidelines

1. **Component Structure**: Functional components dengan hooks
2. **Styling**: Gunakan sx prop atau style props dari MUI
3. **State Management**: Zustand untuk global state
4. **API Calls**: Services pattern di folder `services/`
5. **Routing**: React Router v6 dengan protected routes

## 🐛 Troubleshooting

### CORS Error
Pastikan backend berjalan di `http://localhost:8000` dan CORS sudah dikonfigurasi.

### Module Not Found
```bash
npm install
rm -rf node_modules package-lock.json
npm install
```

### Vite Not Starting
```bash
npm run dev -- --host 0.0.0.0 --port 3000
```

## 📚 Resources

- [Material-UI Documentation](https://mui.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [React Router Documentation](https://reactrouter.com/)

## 📄 License

MIT License

---

**Frontend Ready! Backend juga siap. Mari kita integrasikan keduanya!** 🚀
