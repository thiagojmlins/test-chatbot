import { QueryClient, QueryClientProvider } from 'react-query';
import {
  BrowserRouter as Router,
  Route,
  Routes,
} from 'react-router-dom';
import SignUp from './components/SignUp';
import Login from './components/Login';
import Chat from './components/Chat';
import ProtectedRoute from './components/ProtectedRoute';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-100 flex justify-center items-center">
          <Routes>
            <Route path="/signup" element={<SignUp />} />
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Chat />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
