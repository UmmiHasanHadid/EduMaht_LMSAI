import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar, Toolbar, Typography, Box, IconButton, Avatar, Menu, MenuItem, Divider,
  Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  useMediaQuery, useTheme, Button, Chip,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/Dashboard'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import QuizIcon from '@mui/icons-material/Quiz'
import LogoutIcon from '@mui/icons-material/Logout'
import Brightness4Icon from '@mui/icons-material/Brightness4'
import Brightness7Icon from '@mui/icons-material/Brightness7'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'

import { useAuthStore } from '../stores/authStore'

export default function Layout({ isDarkMode, onToggleDarkMode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { user, logout } = useAuthStore()
  const [anchor, setAnchor] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)

  const items = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'AI Tutor', icon: <SmartToyIcon />, path: '/tutor' },
    { text: 'Kuis', icon: <QuizIcon />, path: '/quizzes' },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname.startsWith(path)

  const drawer = (
    <Box sx={{ width: 260 }} role="presentation" data-testid="mobile-drawer">
      <Box sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <AutoAwesomeIcon color="primary" />
        <Typography variant="h6" sx={{ fontWeight: 800 }}>EduMaht</Typography>
      </Box>
      <Divider />
      <List>
        {items.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              data-testid={`nav-${item.path.replace('/', '')}-btn`}
              selected={isActive(item.path)}
              onClick={() => { navigate(item.path); setMobileOpen(false) }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  const roleLabel = user?.role === 'instructor' ? 'Guru' : user?.role === 'admin' ? 'Admin' : 'Siswa'
  const roleColor = user?.role === 'instructor' ? 'secondary' : user?.role === 'admin' ? 'warning' : 'primary'

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" color="inherit" elevation={0}
        sx={{ backdropFilter: 'blur(10px)', backgroundColor: (t) => t.palette.mode === 'dark' ? 'rgba(17,24,43,0.75)' : 'rgba(255,255,255,0.75)', borderBottom: (t) => `1px solid ${t.palette.divider}` }}
      >
        <Toolbar sx={{ gap: 1 }}>
          {isMobile && (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} data-testid="mobile-menu-btn">
              <MenuIcon />
            </IconButton>
          )}
          <Box
            onClick={() => navigate('/dashboard')}
            sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer', flexGrow: 0 }}
            data-testid="brand-home-link"
          >
            <AutoAwesomeIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: '-0.01em' }}>
              EduMaht
              <Box component="span" sx={{ ml: 0.5, color: 'secondary.main' }}>·AI</Box>
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              {items.map((item) => (
                <Button
                  key={item.path}
                  data-testid={`topnav-${item.path.replace('/', '')}-btn`}
                  startIcon={item.icon}
                  onClick={() => navigate(item.path)}
                  variant={isActive(item.path) ? 'contained' : 'text'}
                  color={isActive(item.path) ? 'primary' : 'inherit'}
                  sx={{ fontWeight: 700 }}
                >
                  {item.text}
                </Button>
              ))}
            </Box>
          )}

          <IconButton onClick={onToggleDarkMode} data-testid="theme-toggle-btn">
            {isDarkMode ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>

          <IconButton onClick={(e) => setAnchor(e.currentTarget)} data-testid="user-menu-btn">
            <Avatar sx={{ width: 34, height: 34, bgcolor: 'primary.main', fontWeight: 700 }}>
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </Avatar>
          </IconButton>
          <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem disabled sx={{ opacity: '1 !important' }}>
              <Box>
                <Typography sx={{ fontWeight: 700 }}>{user?.full_name}</Typography>
                <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
                <Box sx={{ mt: 0.5 }}>
                  <Chip size="small" label={roleLabel} color={roleColor} data-testid="user-role-chip" />
                </Box>
              </Box>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout} data-testid="logout-btn">
              <ListItemIcon><LogoutIcon fontSize="small" color="error" /></ListItemIcon>
              <Typography color="error">Keluar</Typography>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Drawer open={mobileOpen} onClose={() => setMobileOpen(false)}>{drawer}</Drawer>

      <Box component="main" sx={{ px: { xs: 2, md: 4 }, py: { xs: 2, md: 3 }, maxWidth: 1400, mx: 'auto' }}>
        <Outlet />
      </Box>
    </Box>
  )
}
