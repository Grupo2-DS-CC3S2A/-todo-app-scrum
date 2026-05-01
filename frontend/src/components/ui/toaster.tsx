/**
 * Sistema de notificaciones (Toasts) basado en Chakra UI v3.
 *
 * Exporta una unica instancia ``toaster`` reutilizable en toda la app y un
 * componente ``Toaster`` que se monta una sola vez en la raiz.
 */

import type { ReactElement } from "react";
import {
  Toaster as ChakraToaster,
  Portal,
  Spinner,
  Stack,
  Toast,
  createToaster,
} from "@chakra-ui/react";

export const toaster = createToaster({
  placement: "top-end",
  pauseOnPageIdle: true,
});

export function Toaster(): ReactElement {
  return (
    <Portal>
      <ChakraToaster toaster={toaster} insetInline={{ mdDown: "4" }}>
        {(toast) => (
          <Toast.Root width={{ md: "sm" }}>
            {toast.type === "loading" ? (
              <Spinner size="sm" color="blue.solid" />
            ) : (
              <Toast.Indicator />
            )}
            <Stack gap="1" flex="1" maxWidth="100%">
              {toast.title !== undefined && <Toast.Title>{toast.title}</Toast.Title>}
              {toast.description !== undefined && (
                <Toast.Description>{toast.description}</Toast.Description>
              )}
            </Stack>
            {toast.action !== undefined && (
              <Toast.ActionTrigger>{toast.action.label}</Toast.ActionTrigger>
            )}
            <Toast.CloseTrigger />
          </Toast.Root>
        )}
      </ChakraToaster>
    </Portal>
  );
}
