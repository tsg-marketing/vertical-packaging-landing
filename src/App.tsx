
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import MainRedirect from "./pages/MainRedirect";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/main" element={<MainRedirect />} />
          <Route path="/main/courses" element={<MainRedirect to="/main/courses/index.html" />} />
          <Route path="/main/professions" element={<MainRedirect to="/main/professions/index.html" />} />
          <Route path="/main/professions/backend-razrabotchik" element={<MainRedirect to="/main/professions/backend-razrabotchik/index.html" />} />
          <Route path="/main/courses/python-razrabotchik" element={<MainRedirect to="/main/courses/python-razrabotchik/index.html" />} />
          <Route path="/main/compare" element={<MainRedirect to="/main/compare/index.html" />} />
          <Route path="/main/instruction" element={<MainRedirect to="/main/instruction/index.html" />} />
          <Route path="/main/blog" element={<MainRedirect to="/main/blog/index.html" />} />
          <Route path="/main/blog/kak-sravnivat-ceny-kursov" element={<MainRedirect to="/main/blog/kak-sravnivat-ceny-kursov/index.html" />} />
          <Route path="/main/schools" element={<MainRedirect to="/main/schools/index.html" />} />
          <Route path="/main/schools/school_name" element={<MainRedirect to="/main/schools/school_name/index.html" />} />
          <Route path="/courses" element={<MainRedirect to="/main/courses/index.html" />} />
          <Route path="/professions" element={<MainRedirect to="/main/professions/index.html" />} />
          <Route path="/main/admin-demo" element={<MainRedirect to="/main/admin-demo/index.html" />} />
          <Route path="/main/courses/kurs-json" element={<MainRedirect to="/main/courses/kurs-json/index.html" />} />
          <Route path="/main/courses/kurs-json-partial" element={<MainRedirect to="/main/courses/kurs-json-partial/index.html" />} />
          <Route path="/main/podborki" element={<MainRedirect to="/main/podborki/index.html" />} />
          <Route path="/main/podborki/besplatnye" element={<MainRedirect to="/main/podborki/besplatnye/index.html" />} />
          <Route path="/main/podborki/dlya-detej" element={<MainRedirect to="/main/podborki/dlya-detej/index.html" />} />
          <Route path="/main/podborki/dlya-detej/11-14-let" element={<MainRedirect to="/main/podborki/dlya-detej/11-14-let/index.html" />} />
          <Route path="/main/podborki/dlya-detej/11-14-let/programmirovanie" element={<MainRedirect to="/main/podborki/dlya-detej/11-14-let/programmirovanie/index.html" />} />
          <Route path="/main/podborki/dlya-detej/11-14-let/razrabotka-igr" element={<MainRedirect to="/main/podborki/dlya-detej/11-14-let/razrabotka-igr/index.html" />} />
          <Route path="/main/podborki/dlya-detej/7-10-let" element={<MainRedirect to="/main/podborki/dlya-detej/7-10-let/index.html" />} />
          <Route path="/main/podborki/dlya-detej/7-10-let/programmirovanie" element={<MainRedirect to="/main/podborki/dlya-detej/7-10-let/programmirovanie/index.html" />} />
          <Route path="/main/podborki/dlya-detej/7-10-let/risovanie" element={<MainRedirect to="/main/podborki/dlya-detej/7-10-let/risovanie/index.html" />} />
          <Route path="/main/podborki/dlya-detej/ege-oge" element={<MainRedirect to="/main/podborki/dlya-detej/ege-oge/index.html" />} />
          <Route path="/main/podborki/dlya-nachinayushchih" element={<MainRedirect to="/main/podborki/dlya-nachinayushchih/index.html" />} />
          <Route path="/main/podborki/dlya-nachinayushchih/dlya-gumanitariev" element={<MainRedirect to="/main/podborki/dlya-nachinayushchih/dlya-gumanitariev/index.html" />} />
          <Route path="/main/podborki/dlya-nachinayushchih/it-bez-opyta" element={<MainRedirect to="/main/podborki/dlya-nachinayushchih/it-bez-opyta/index.html" />} />
          <Route path="/main/podborki/dlya-nachinayushchih/posle-40" element={<MainRedirect to="/main/podborki/dlya-nachinayushchih/posle-40/index.html" />} />
          <Route path="/main/podborki/korotkie" element={<MainRedirect to="/main/podborki/korotkie/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/posle-stazhirovki" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/posle-stazhirovki/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/posle-stazhirovki/ne-v-it" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/posle-stazhirovki/ne-v-it/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/posle-stazhirovki/v-it" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/posle-stazhirovki/v-it/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/s-garantiej" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/s-garantiej/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/srazu" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/srazu/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/srazu/ne-v-it" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/srazu/ne-v-it/index.html" />} />
          <Route path="/main/podborki/s-trudoustrojstvom/srazu/v-it" element={<MainRedirect to="/main/podborki/s-trudoustrojstvom/srazu/v-it/index.html" />} />
          <Route path="/main/podborki/v-rassrochku" element={<MainRedirect to="/main/podborki/v-rassrochku/index.html" />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;