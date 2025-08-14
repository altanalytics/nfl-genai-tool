import React from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import AuthenticatedApp from './components/Auth/AuthenticatedApp';
import './App.css';

// Create NFL-themed dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#013369', // NFL Blue
    },
    secondary: {
      main: '#D50A0A', // NFL Red
    },
    background: {
      default: '#013369',
      paper: '#1a4480',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
          minHeight: '100vh',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Authenticator
        signUpAttributes={['email', 'name']}
        components={{
          SignUp: {
            FormFields() {
              return (
                <>
                  <Authenticator.SignUp.FormFields />
                </>
              );
            },
          },
        }}
      >
        {({ signOut }) => <AuthenticatedApp signOut={signOut} />}
      </Authenticator>
    </ThemeProvider>
  );
}

export default App;
