import './App.css';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';

import HomePage from './pages/HomePage';
import ChatWithAIPage from './pages/ChatWithAIPage';
import UploadPage from './pages/UploadPage';
import ReindexPage from './pages/ReindexPage';
import FeedbackPage from './pages/FeedbackPage';
import HealthPage from './pages/HealthPage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import OptionsPage from './pages/OptionsPage';
import AnalysisPage from './pages/AnalysisPage';
import Layout from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SidebarProvider } from './context/SidebarContext';
import { SettingsProvider } from './context/SettingsContext';

function PrivateRoute({ element }) {
  const { token } = useAuth();
  const location = useLocation();
  return token ? element : <LoginPage redirectPath={location.pathname} />;
}

function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <SidebarProvider>
          <Router>
            <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/ask" element={<PrivateRoute element={<ChatWithAIPage />} />} />
            <Route path="/upload" element={<PrivateRoute element={<UploadPage />} />} />
            <Route path="/reindex" element={<PrivateRoute element={<ReindexPage />} />} />
            <Route path="/feedback" element={<PrivateRoute element={<FeedbackPage />} />} />
            <Route path="/analysis" element={<PrivateRoute element={<AnalysisPage />} />} />
            <Route path="/profile" element={<PrivateRoute element={<ProfilePage />} />} />
            <Route path="/options" element={<PrivateRoute element={<OptionsPage />} />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/login" element={<LoginPage />} />
          </Routes>
            </Layout>
          </Router>
        </SidebarProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;