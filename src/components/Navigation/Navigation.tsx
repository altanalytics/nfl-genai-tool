import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Avatar,
  Chip,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  GitHub,
  Language,
  Logout,
  MoreVert,
} from '@mui/icons-material';

interface NavigationProps {
  userName: string;
  signOut: () => void;
}

const Navigation: React.FC<NavigationProps> = ({ userName, signOut }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExternalLink = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
    handleMenuClose();
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        background: '#013369', // Solid NFL blue
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
      }}
    >
      <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 1.5 } }}>
          <Avatar sx={{ 
            background: 'transparent',
            width: { xs: 28, sm: 36 }, 
            height: { xs: 28, sm: 36 },
            boxShadow: '0 4px 12px rgba(255, 255, 255, 0.2)',
          }}>
            <img 
              src="/footballlogo.png" 
              alt="NFL Logo" 
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'contain' 
              }} 
            />
          </Avatar>
          <Box>
            <Typography variant="h6" component="div" sx={{ 
              fontWeight: 700,
              fontSize: { xs: '0.9rem', sm: '1.1rem' },
              lineHeight: 1.2,
              color: '#f8fafc'
            }}>
              NFL GenAI Tool
            </Typography>
            {!isMobile && (
              <Typography variant="caption" sx={{ 
                color: '#94a3b8',
                fontSize: '0.75rem',
                fontWeight: 500
              }}>
                powered by Amazon Bedrock and strands-agents
              </Typography>
            )}
          </Box>
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Desktop Navigation */}
        {!isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              color="inherit"
              href="https://github.com/altanalytics/strands-agentcore-react"
              target="_blank"
              rel="noopener noreferrer"
              sx={{ 
                color: '#e2e8f0',
                '&:hover': { 
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  transform: 'translateY(-1px)',
                  color: '#f8fafc',
                },
                transition: 'all 0.2s ease',
              }}
            >
              <GitHub />
            </IconButton>

            <IconButton
              color="inherit"
              href="https://www.altanalyticsllc.com"
              target="_blank"
              rel="noopener noreferrer"
              sx={{ 
                color: '#e2e8f0',
                '&:hover': { 
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  transform: 'translateY(-1px)',
                  color: '#f8fafc',
                },
                transition: 'all 0.2s ease',
              }}
            >
              <Language />
            </IconButton>

            {/* User Info */}
            <Chip
              label={userName}
              variant="outlined"
              sx={{ 
                color: '#f8fafc',
                borderColor: 'rgba(255, 255, 255, 0.4)',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                ml: 2,
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                }
              }}
            />

            {/* Sign Out Button */}
            <Button
              variant="contained"
              color="error"
              startIcon={<Logout />}
              onClick={signOut}
              sx={{ 
                ml: 1,
                background: 'linear-gradient(135deg, #D50A0A 0%, #b91c1c 100%)',
                fontWeight: 600,
                '&:hover': {
                  background: 'linear-gradient(135deg, #b91c1c 0%, #991b1b 100%)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 12px rgba(213, 10, 10, 0.4)',
                },
                transition: 'all 0.2s ease',
              }}
            >
              Sign Out
            </Button>
          </Box>
        )}

        {/* Mobile Navigation */}
        {isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* User name chip - smaller on mobile */}
            <Chip
              label={userName}
              variant="outlined"
              size="small"
              sx={{ 
                color: '#f8fafc',
                borderColor: 'rgba(255, 255, 255, 0.4)',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                fontWeight: 500,
                fontSize: '0.75rem',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                }
              }}
            />

            {/* Mobile menu button */}
            <IconButton
              color="inherit"
              onClick={handleMenuOpen}
              sx={{ 
                color: '#e2e8f0',
                '&:hover': { 
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                },
              }}
            >
              <MoreVert />
            </IconButton>

            {/* Mobile menu */}
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              <MenuItem onClick={() => handleExternalLink('https://github.com/altanalytics/strands-agentcore-react')}>
                <GitHub sx={{ mr: 1 }} />
                GitHub
              </MenuItem>
              <MenuItem onClick={() => handleExternalLink('https://www.altanalyticsllc.com')}>
                <Language sx={{ mr: 1 }} />
                Alt Analytics
              </MenuItem>
              <MenuItem onClick={() => { signOut(); handleMenuClose(); }}>
                <Logout sx={{ mr: 1 }} />
                Sign Out
              </MenuItem>
            </Menu>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
