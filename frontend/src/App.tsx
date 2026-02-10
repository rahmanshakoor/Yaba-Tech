import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PageLayout } from './components/layout';
import Dashboard from './pages/Dashboard';
import DefinitionsPage from './pages/DefinitionsPage';
import InventoryPage from './pages/InventoryPage';
import RecipesPage from './pages/RecipesPage';
import ProductionPage from './pages/ProductionPage';
import InvoicesPage from './pages/InvoicesPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PageLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/definitions" element={<DefinitionsPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/recipes" element={<RecipesPage />} />
            <Route path="/production" element={<ProductionPage />} />
            <Route path="/invoices" element={<InvoicesPage />} />
          </Routes>
        </PageLayout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
