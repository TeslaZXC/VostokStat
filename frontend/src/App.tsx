import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { MissionsPage } from './pages/MissionsPage';
import { MissionDetailPage } from './pages/MissionDetailPage';
import { TopSquads } from './pages/TopSquads';
import { TopPlayers } from './pages/TopPlayers';
import { SquadProfile } from './pages/SquadProfile';
import { PlayerProfile } from './pages/PlayerProfile';
import TotalStats from './pages/TotalStats';
import AdminDashboard from './pages/AdminDashboard';
import AdminLogin from './pages/AdminLogin';
import AdminMissions from './pages/AdminMissions';
import AdminPlayers from './pages/AdminPlayers';
import AdminConfig from './pages/AdminConfig';
import AdminUsers from './pages/AdminUsers';
import AdminTools from './pages/AdminTools';
import AdminMissionSquadStats from './pages/AdminMissionSquadStats';
import { AdminLayout } from './pages/AdminLayout';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        {/* Main Site Routes - Wrapped in Layout */}
        <Route path="/" element={<Layout><Home /></Layout>} />
        <Route path="/total-stats" element={<Layout><TotalStats /></Layout>} />
        <Route path="/missions" element={<Layout><MissionsPage /></Layout>} />
        <Route path="/missions/:id" element={<Layout><MissionDetailPage /></Layout>} />
        <Route path="/squads" element={<Layout><TopSquads /></Layout>} />
        <Route path="/squads/:name" element={<Layout><SquadProfile /></Layout>} />
        <Route path="/players" element={<Layout><TopPlayers /></Layout>} />
        <Route path="/players/:name" element={<Layout><PlayerProfile /></Layout>} />

        {/* Admin Routes - Isolated from Main Layout */}
        <Route path="/admin/login" element={<AdminLogin />} />

        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} /> {/* Squads */}
          <Route path="missions" element={<AdminMissions />} />
          <Route path="mission-squad-stats" element={<AdminMissionSquadStats />} />
          <Route path="players" element={<AdminPlayers />} />
          <Route path="config" element={<AdminConfig />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="tools" element={<AdminTools />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
