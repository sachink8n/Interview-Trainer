import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import SetupPage from './pages/SetupPage'
import InterviewPage from './pages/InterviewPage'
import ResultsPage from './pages/ResultsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"                        element={<HomePage />} />
        <Route path="/setup"                   element={<SetupPage />} />
        <Route path="/interview/:sessionId"    element={<InterviewPage />} />
        <Route path="/results/:sessionId"      element={<ResultsPage />} />
      </Routes>
    </BrowserRouter>
  )
}
