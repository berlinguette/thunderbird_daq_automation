import React from 'react';
import ReactDOM from 'react-dom/client'
import Home from './pages/Home.tsx'
import { ChakraProvider } from '@chakra-ui/react'
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import Queue from './pages/Queue.tsx';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LogListener from './layout/LogListener.tsx';

const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
  },
  {
    path: "/queue",
    element: <Queue />
  }
]);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1
    }
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ChakraProvider>
        <LogListener>
          <RouterProvider router={router} />
        </LogListener>
      </ChakraProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
