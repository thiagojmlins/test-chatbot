import { QueryClient, QueryClientProvider } from 'react-query';
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from 'react-router-dom';
import SignUp from './components/SignUp';
import Login from './components/Login';
import Chat from './components/Chat';
import { useEffect, useState } from 'react';

const queryClient = new QueryClient();

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<
    boolean | null
  >(null);

  // Check if the user is authenticated by checking for a token in localStorage
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  // If the authentication status hasn't been determined, show a loading state
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-100 flex justify-center items-center">
          <Routes>
            {/* Automatically redirect based on authentication status */}
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <Navigate to="/chat" />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/chat"
              element={
                isAuthenticated ? (
                  <Chat />
                ) : (
                  // Redirect to login if not authenticated
                  <Navigate to="/login" />
                )
              }
            />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
