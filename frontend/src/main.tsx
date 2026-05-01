import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ChakraProvider, defaultSystem } from "@chakra-ui/react";

import App from "@/App";
import { Toaster } from "@/components/ui/toaster";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("No se encontro el elemento raiz #root en index.html.");
}

createRoot(rootElement).render(
  <StrictMode>
    <ChakraProvider value={defaultSystem}>
      <App />
      <Toaster />
    </ChakraProvider>
  </StrictMode>,
);
