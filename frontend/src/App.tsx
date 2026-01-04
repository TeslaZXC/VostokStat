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
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/total-stats" element={<TotalStats />} />
          <Route path="/missions" element={<MissionsPage />} />
          <Route path="/missions/:id" element={<MissionDetailPage />} />
          <Route path="/squads" element={<TopSquads />} />
          <Route path="/squads/:name" element={<SquadProfile />} />
          <Route path="/players" element={<TopPlayers />} />
          <Route path="/players/:name" element={<PlayerProfile />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
